# wakeword-capture — rolling mic buffer for wake-word feedback on smartdash.
FROM python:3.11-slim-bookworm

# Link the published image to this repository so the GHCR package inherits its
# (public) visibility. See ../README.md.
LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images
LABEL org.opencontainers.image.title="wakeword-capture"

RUN apt-get update \
    && apt-get install -y --no-install-recommends pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY capture.py /app/capture.py

EXPOSE 8089
CMD ["python3", "/app/capture.py"]
