#!/usr/bin/env python3
"""wakeword-capture — rolling-buffer microphone capture for wake-word feedback.

Runs on the `smartdash` kiosk next to Linux Voice Assistant, reading the same
ReSpeaker source (channel 0, the channel LVA feeds to the wake-word engine) into
a RAM-only ring buffer. Nothing is written to disk until Home Assistant (or a
person) calls POST /mark. This keeps the privacy cost to "a few seconds in RAM"
while making both false negatives and false positives easy to collect.

Endpoints (default port 8089, LAN-only):
  GET  /health                 -> buffer/source status
  POST /mark?label=fn|fp|neg&note=...&pre=3&post=1&anchor=2.0
                               -> write <FEEDBACK_DIR>/<label>-<ts>.wav + manifest line

Label semantics (see docs/wakeword-feedback-loop.md):
  fn  false negative — the wake word was said and did not fire  -> training positive
  fp  false positive — fired without the wake word             -> training negative
  neg deliberate household negative capture                    -> training negative

`anchor` is the seconds-from-clip-start where the wake word is believed to be
(defaults to `pre`, i.e. the moment of the mark). It is only a hint for review
and for windowing in ingest_feedback.py; the clip is kept whole.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
import wave
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2


class Ring:
    """Thread-safe rolling buffer of mono 16 kHz s16le audio, in RAM only."""

    def __init__(self, source: str, channels: int, seconds: float, chunk_frames: int = 1600):
        self.source = source
        self.channels = channels
        self.seconds = seconds
        self.chunk_frames = chunk_frames
        self._buf: deque[tuple[float, bytes]] = deque()
        self._total = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        cmd = [
            "parec", "--raw",
            f"--device={self.source}",
            f"--rate={SAMPLE_RATE}",
            f"--channels={self.channels}",
            "--format=s16le",
        ]
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        assert self._proc and self._proc.stdout
        frame_bytes = self.channels * BYTES_PER_SAMPLE
        want = self.chunk_frames * frame_bytes
        while not self._stop.is_set():
            raw = self._proc.stdout.read(want)
            if not raw:
                time.sleep(0.05)
                continue
            # Keep channel 0 only (matches LVA's wake-word input channel).
            mono = raw[0::frame_bytes]
            if self.channels > 1:
                mono = bytes(
                    b
                    for i in range(0, len(raw) - frame_bytes + 1, frame_bytes)
                    for b in raw[i:i + BYTES_PER_SAMPLE]
                )
            dur = len(mono) / (SAMPLE_RATE * BYTES_PER_SAMPLE)
            now = time.monotonic()
            with self._lock:
                self._buf.append((now, mono))
                self._total += dur
                while self._total > self.seconds and self._buf:
                    _, old = self._buf.popleft()
                    self._total -= len(old) / (SAMPLE_RATE * BYTES_PER_SAMPLE)

    def snapshot(self) -> bytes:
        with self._lock:
            return b"".join(chunk for _, chunk in self._buf)

    def status(self) -> dict:
        with self._lock:
            return {
                "source": self.source,
                "channels": self.channels,
                "ring_seconds": round(self._total, 2),
                "chunks": len(self._buf),
            }


def write_wav(path: str, pcm: bytes) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(BYTES_PER_SAMPLE)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)


class Handler(BaseHTTPRequestHandler):
    ring: Ring
    feedback_dir: str
    lock = threading.Lock()

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # keep the container log quiet
        pass

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/health":
            self._json(200, {"ok": True, **self.ring.status()})
        else:
            self._json(404, {"ok": False})

    def do_POST(self) -> None:
        u = urlparse(self.path)
        if u.path != "/mark":
            return self._json(404, {"ok": False})
        q = parse_qs(u.query)
        label = (q.get("label", ["fp"])[0] or "fp").lower()
        if label not in ("fn", "fp", "neg"):
            return self._json(400, {"ok": False, "error": "label must be fn|fp|neg"})
        note = q.get("note", [""])[0]
        pre = float(q.get("pre", ["3"])[0])
        post = float(q.get("post", ["1"])[0])
        anchor = float(q.get("anchor", [str(pre)])[0])

        # Wait for the post-roll to land in the buffer, then snapshot it.
        time.sleep(max(0.0, post))
        pcm = self.ring.snapshot()
        max_bytes = int((pre + post) * SAMPLE_RATE * BYTES_PER_SAMPLE)
        if len(pcm) > max_bytes:
            pcm = pcm[-max_bytes:]

        ts = time.strftime("%Y%m%d-%H%M%S")
        name = f"{label}-{ts}.wav"
        os.makedirs(self.feedback_dir, exist_ok=True)
        path = os.path.join(self.feedback_dir, name)
        with self.lock:
            write_wav(path, pcm)
            rec = {
                "file": name, "label": label, "note": note,
                "ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "duration_s": round(len(pcm) / (SAMPLE_RATE * BYTES_PER_SAMPLE), 3),
                "anchor_s": anchor, "pre_s": pre, "post_s": post,
                "source": self.ring.source, "channels": self.ring.channels,
            }
            with open(os.path.join(self.feedback_dir, "manifest.jsonl"), "a") as fh:
                fh.write(json.dumps(rec) + "\n")
        self._json(200, {"ok": True, "file": name, **rec})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.environ.get("CAPTURE_SOURCE", ""))
    ap.add_argument("--channels", type=int, default=int(os.environ.get("CAPTURE_CHANNELS", "3")))
    ap.add_argument("--ring-seconds", type=float, default=float(os.environ.get("RING_SECONDS", "8")))
    ap.add_argument("--feedback-dir", default=os.environ.get("FEEDBACK_DIR", "/data/feedback"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("CAPTURE_PORT", "8089")))
    args = ap.parse_args()
    if not args.source:
        raise SystemExit("CAPTURE_SOURCE / --source is required")

    ring = Ring(args.source, args.channels, args.ring_seconds)
    ring.start()
    Handler.ring = ring
    Handler.feedback_dir = args.feedback_dir
    print(f"wakeword-capture on :{args.port} source={args.source} ring={args.ring_seconds}s", flush=True)
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
