# openWakeWord "Manolo" training environment — pinned, amd64-only, beast-side.
#
# Rationale for the pins: docs/manolo-wake-word-plan.md §3.2 and §1.4. The
# upstream pipeline is bit-rotted on modern Python; Python 3.10 is the last
# version for which every pinned wheel exists. Do NOT "upgrade to latest".
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
ARG OWW_COMMIT=main
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
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

# openWakeWord (importable as `openwakeword`) + piper-sample-generator (must be
# importable at /opt/piper-sample-generator for train.py's root import).
RUN git clone https://github.com/dscripka/openWakeWord /opt/openWakeWord \
    && git -C /opt/openWakeWord checkout "${OWW_COMMIT}" \
    && pip install -e /opt/openWakeWord \
    && git clone https://github.com/rhasspy/piper-sample-generator /opt/piper-sample-generator \
    && git -C /opt/piper-sample-generator checkout "${PSG_COMMIT}" \
    && pip install -e /opt/piper-sample-generator

ENV PYTHONPATH=/opt/piper-sample-generator:/opt/openWakeWord

# The tools we own (the Spanish clip generator and the feedback ingester) are
# NOT baked in: they live with the repo that uses them and are bind-mounted at
# /opt/oww-tools (see hosts/beast/oww-training/compose.yml in home-ops), so they
# can be edited without rebuilding this image.

WORKDIR /work
# Keep the container alive; training steps are run interactively via
# `docker compose exec` (see README).
CMD ["sleep", "infinity"]
