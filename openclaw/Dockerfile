ARG OPENCLAW_VERSION=2026.5.6

FROM ghcr.io/openclaw/openclaw:${OPENCLAW_VERSION}

LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images

USER root

RUN \
  /usr/bin/apt-get -y update && \
  /usr/bin/apt-get -y install --no-install-recommends \
    ffmpeg \
    jq \
    less \
    openssh-client \
    python3 \
    vim-tiny && \
  /usr/bin/rm -rf /var/lib/apt/lists/* && \
  ARCH=$(dpkg --print-architecture) && \
  curl -fsSL "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${ARCH}" \
    -o /usr/local/bin/yq && \
  chmod +x /usr/local/bin/yq && \
  curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl" \
    -o /usr/local/bin/kubectl && \
  chmod +x /usr/local/bin/kubectl

USER node
