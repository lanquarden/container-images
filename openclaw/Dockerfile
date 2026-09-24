ARG OPENCLAW_VERSION=2026.9.6

FROM ghcr.io/openclaw/openclaw:${OPENCLAW_VERSION}@sha256:0a5ff5e682e62afa19149df126aa50063bf65ef885b5c94713ce32dc0eb12e15

LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images

USER root

RUN \
  /usr/bin/apt-get -y update && \
  /usr/bin/apt-get -y install --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    jq \
    less \
    openssh-client \
    python3 \
    vim-tiny && \
  /usr/bin/install -d -m 0755 /etc/apt/keyrings /etc/apt/sources.list.d && \
  /usr/bin/curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
  echo "6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b  /etc/apt/keyrings/githubcli-archive-keyring.gpg" \
    | /usr/bin/sha256sum -c - && \
  /usr/bin/chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list && \
  /usr/bin/apt-get -y update && \
  /usr/bin/apt-get -y install --no-install-recommends gh && \
  ARCH=$(dpkg --print-architecture) && \
  curl -fsSL "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${ARCH}" \
    -o /usr/local/bin/yq && \
  chmod +x /usr/local/bin/yq && \
  curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl" \
    -o /usr/local/bin/kubectl && \
  chmod +x /usr/local/bin/kubectl && \
  /usr/bin/rm -rf /var/lib/apt/lists/* /var/cache/apt/*

USER node
