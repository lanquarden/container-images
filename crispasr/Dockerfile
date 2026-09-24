# CrispASR ASR + TTS service image (Vulkan, AMD RDNA via RADV).
#
# One image serves both halves of the pipeline; compose.yml runs two instances
# (different --backend). Models are pulled on first start into the
# CRISPASR_MODELS_DIR volume and reused afterwards.
FROM ubuntu:26.04

# Link the published image to this repository so the GHCR package inherits its
# (public) visibility. See ../README.md.
LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images
LABEL org.opencontainers.image.title="CrispASR ASR/TTS (Vulkan)"

ARG CRISPASR_VERSION=0.8.34

# libvulkan1 + mesa-vulkan-drivers provide the RADV userspace driver; the
# amdgpu kernel driver and /dev/dri come from the host.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libvulkan1 \
        mesa-vulkan-drivers \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL -o /tmp/crispasr.tar.gz \
      "https://github.com/CrispStrobe/CrispASR/releases/download/v${CRISPASR_VERSION}/crispasr-linux-x86_64-vulkan.tar.gz"; \
    mkdir -p /opt/crispasr; \
    tar xzf /tmp/crispasr.tar.gz -C /tmp; \
    cp -a /tmp/crispasr-linux-x86_64-vulkan/. /opt/crispasr/; \
    rm -rf /tmp/crispasr.tar.gz /tmp/crispasr-linux-x86_64-vulkan; \
    chmod +x /opt/crispasr/crispasr /opt/crispasr/crispasr-quantize; \
    /opt/crispasr/crispasr --version | head -3

COPY entrypoint.sh /usr/local/bin/crispasr-entrypoint.sh
RUN chmod +x /usr/local/bin/crispasr-entrypoint.sh

ENV LD_LIBRARY_PATH=/opt/crispasr \
    CRISPASR_MODELS_DIR=/models \
    CRISPASR_CACHE_DIR=/models

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/crispasr-entrypoint.sh"]
