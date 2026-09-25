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

# One pip resolution for everything. A *separate*, later `pip install -e
# /opt/openWakeWord` re-resolves on its own and pulls numpy 2.x (scipy 1.15
# allows numpy<2.5 and nothing else pins it), which then breaks
# tensorflow / pyarrow / openwakeword imports compiled against numpy 1.x.
# Installing requirements + openWakeWord together keeps the `numpy<2` pin in
# force for the whole graph.
#
# openWakeWord (importable as `openwakeword`) + piper-sample-generator (must be
# importable at /opt/piper-sample-generator for train.py's root import).
RUN pip install --upgrade pip \
    && git clone https://github.com/dscripka/openWakeWord /opt/openWakeWord \
    && git -C /opt/openWakeWord checkout "${OWW_COMMIT}" \
    && git clone https://github.com/rhasspy/piper-sample-generator /opt/piper-sample-generator \
    && git -C /opt/piper-sample-generator checkout "${PSG_COMMIT}" \
    && pip install -r /tmp/requirements.txt -e /opt/openWakeWord

# piper-sample-generator v2.0.0 ships no setup.py/pyproject.toml, so it is not
# pip-installable. openWakeWord's train.py only needs its root-level
# generate_samples.py importable (it does `sys.path.insert(0,
# piper_sample_generator_path)` then `from generate_samples import
# generate_samples`); PYTHONPATH below provides that. The module's runtime deps
# (torchaudio, piper-phonemize) are pinned in requirements.txt instead.

ENV PYTHONPATH=/opt/piper-sample-generator:/opt/openWakeWord

# The tools we own (the Spanish clip generator and the feedback ingester) are
# NOT baked in: they live with the repo that uses them and are bind-mounted at
# /opt/oww-tools (see hosts/beast/oww-training/compose.yml in home-ops), so they
# can be edited without rebuilding this image.

WORKDIR /work
# Keep the container alive; training steps are run interactively via
# `docker compose exec` (see README).
CMD ["sleep", "infinity"]
