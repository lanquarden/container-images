# openWakeWord "Manolo" training environment — pinned, amd64-only, beast-side.
#
# Rationale for the pins: docs/manolo-wake-word-plan.md §3.2 and §1.4, plus the
# defects the first real run hit on 2026-10-04 and this revision fixes:
#   - numpy resolved to 2.2.6 via openwakeword -> ai-edge-litert -> ml_dtypes
#     0.6.0, which broke the pinned pyarrow. The pins in requirements.txt are
#     installed AFTER openWakeWord so they win the resolution.
#   - `mutagen` was missing, so `import openwakeword.train` failed.
#   - the openWakeWord checkout ships no openwakeword/resources/models/, so
#     AudioFeatures could not load melspectrogram.onnx / embedding_model.onnx.
#   - upstream's ONNX->TFLite path (tensorflow-cpu 2.8.1 + onnx_tf 1.10) aborts
#     on a protobuf ABI mismatch; replaced by onnx2tf.
#
# This image only ever runs on `beast` (or another amd64 Linux host). It is not
# installed on the kiosk and is not part of the Talos cluster.
FROM python:3.10-slim-bookworm

# Link the published image to this repository so the GHCR package inherits its
# (public) visibility. See ../README.md.
LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images
LABEL org.opencontainers.image.title="openWakeWord training env"

# Pin both upstream checkouts. Verify these resolve before the first build:
#   - openWakeWord: a commit whose train.py still imports the root-level
#     piper-sample-generator `generate_samples` module (imported unconditionally).
#   - piper-sample-generator: a commit that still exposes generate_samples.py at
#     its repository root (v2.x; v3.x reorganised the package).
ARG OWW_COMMIT=368c03716d1e92591906a84949bc477f3a834455
ARG PSG_COMMIT=v2.0.0

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WORK=/data/manolo

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
        ffmpeg sox libsndfile1 libgomp1 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

# openWakeWord (importable as `openwakeword`) + piper-sample-generator (must be
# importable at /opt/piper-sample-generator for train.py's root import) first,
# so their base dependencies resolve; then the pinned requirements on top, so
# an unpinned transitive dependency (numpy via ml_dtypes) cannot win.
RUN pip install --upgrade pip \
    && git clone https://github.com/dscripka/openWakeWord /opt/openWakeWord \
    && git -C /opt/openWakeWord checkout "${OWW_COMMIT}" \
    && pip install -e /opt/openWakeWord \
    && git clone https://github.com/rhasspy/piper-sample-generator /opt/piper-sample-generator \
    && git -C /opt/piper-sample-generator checkout "${PSG_COMMIT}" \
    && pip install -r /tmp/requirements.txt

# piper-sample-generator v2.0.0 ships no setup.py/pyproject.toml, so it is not
# pip-installable. openWakeWord's train.py only needs its root-level
# generate_samples.py importable (it does `sys.path.insert(0,
# piper_sample_generator_path)` then `from generate_samples import
# generate_samples`); PYTHONPATH below provides that.

# The GitHub checkout has no openwakeword/resources/models/, so AudioFeatures
# cannot load melspectrogram.onnx / embedding_model.onnx and --augment_clips
# dies with an onnxruntime NoSuchFile. Fetch the feature + VAD models at build
# time (plus one wake-word model, which the downloader writes alongside them).
RUN python3 -c "import openwakeword.utils as utils; utils.download_models(model_names=['hey_jarvis_v0.1'])"

# ONNX -> TFLite: the kiosk's Linux Voice Assistant loads wake words through
# pyopen_wakeword, which only accepts tflite, and upstream's converter is dead.
COPY onnx2tflite /usr/local/bin/onnx2tflite
RUN chmod +x /usr/local/bin/onnx2tflite

ENV PYTHONPATH=/opt/piper-sample-generator:/opt/openWakeWord

# The tools we own (the Spanish clip generator and the feedback ingester) are
# NOT baked in: they live with the repo that uses them and are bind-mounted at
# /opt/oww-tools (see hosts/beast/oww-training/compose.yml in home-ops), so they
# can be edited without rebuilding this image.

WORKDIR /work
# Keep the container alive; training steps are run interactively via
# `docker compose exec` (see README).
CMD ["sleep", "infinity"]
