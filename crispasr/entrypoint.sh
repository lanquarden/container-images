#!/usr/bin/env bash
# Entrypoint for the CrispASR ASR/TTS service on `beast`.
#
# Everything is driven by environment variables so the same image can serve any
# backend. Recommended pair (see ../README.md and docs/stt-tts-stack-research.md):
#   ASR: qwen3-1.7b  (Qwen3-ASR 1.7B, Q8_0, ~6 GiB, RTF ~0.04, EN+ES)
#   TTS: voxtral-tts (Voxtral-4B-TTS, Q8_0, ~4.7 GiB, RTF ~0.20)
set -euo pipefail

: "${BACKEND:?BACKEND is required, e.g. qwen3-1.7b or voxtral-tts}"
MODEL="${MODEL:-auto}"
MODEL_QUANT="${MODEL_QUANT:-q8_0}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
GPU_BACKEND="${GPU_BACKEND:-vulkan}"

args=(
  --server
  --backend "${BACKEND}"
  -m "${MODEL}"
  --model-quant "${MODEL_QUANT}"
  --auto-download
  --host "${HOST}"
  --port "${PORT}"
  --gpu-backend "${GPU_BACKEND}"
)

# --no-warmup avoids the known Vulkan warmup hang (CrispASR #165); the first
# request then pays the one-off graph build.
[ "${NO_WARMUP:-1}" = "1" ] && args+=(--no-warmup)

# Home Assistant Assist (Wyoming) and realtime streaming ports.
if [ -n "${WYOMING_PORT:-}" ] && [ "${WYOMING_PORT}" != "-1" ]; then
  args+=(--wyoming-port "${WYOMING_PORT}")
fi

# Advertised/used language (ISO 639-1). CrispASR advertises exactly ONE language
# over Wyoming, and Home Assistant only offers an STT/TTS engine whose
# advertised languages match the Assist pipeline language (it validates with
# language_util.matches and drops the engine otherwise). Without this the
# services advertise "en" and cannot be selected for a Spanish pipeline.
# NOTE: advertising "es" means an English pipeline cannot use this instance;
# run a second instance with LANGUAGE=en if per-language STT is ever needed.
if [ -n "${LANGUAGE:-}" ]; then
  args+=(--language "${LANGUAGE}")
fi
if [ -n "${WS_PORT:-}" ] && [ "${WS_PORT}" != "-1" ]; then
  args+=(--ws-port "${WS_PORT}")
fi

# Default TTS voice (CrispASR preset name, or a --voice-dir entry). Advertised to
# Home Assistant over Wyoming; the server still honours a per-request voice.
if [ -n "${VOICE:-}" ]; then
  args+=(--voice "${VOICE}")
fi

# Restricted-licence models (Voxtral TTS is CC-BY-NC-4.0) require explicit
# acceptance before CrispASR will download them.
if [ -n "${ACCEPT_LICENSE:-}" ]; then
  args+=(--accept-license "${ACCEPT_LICENSE}")
fi

# AI-content marking: the default keeps upstream behaviour (audio watermark +
# C2PA). TTS_MARKING=off disables both and takes over the marking duty (the
# attestation flag CrispASR requires is supplied here).
if [ "${TTS_MARKING:-on}" = "off" ]; then
  args+=(--no-watermark --no-c2pa --accept-marking-responsibility)
fi

echo "[crispasr] backend=${BACKEND} model=${MODEL} quant=${MODEL_QUANT} port=${PORT} gpu=${GPU_BACKEND} marking=${TTS_MARKING:-on}"
# EXTRA_ARGS is intentionally word-split.
# shellcheck disable=SC2086
exec /opt/crispasr/crispasr "${args[@]}" ${EXTRA_ARGS:-}
