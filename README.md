# container-images

Custom container images for [`lanquarden/home-ops`](https://github.com/lanquarden/home-ops).
Each subdirectory is one image with its own build workflow, published to GitHub
Container Registry under `ghcr.io/lanquarden/<name>`.

The rule: an image that home-ops builds itself lives here instead, is published
by CI, and is *consumed* by home-ops as a pinned tag — so the definition has one
home and the host never builds from a Dockerfile.

## Images

| Directory | Published as | Platforms | Consumed by |
| --- | --- | --- | --- |
| `openclaw/` | `ghcr.io/lanquarden/openclaw:<upstream>-tools` | linux/amd64 | `hosts/beast/openclaw-node/` (the Build Node Quadlet) |
| `oww-training/` | `ghcr.io/lanquarden/oww-training:latest`, `:sha-<rev>` | linux/amd64 | `hosts/beast/oww-training/` (Spanish wake-word training) |
| `crispasr/` | `ghcr.io/lanquarden/crispasr:<version>` | linux/amd64 | `hosts/beast/crispasr/` (Assist STT/TTS) |
| `wakeword-capture/` | `ghcr.io/lanquarden/wakeword-capture:latest`, `:sha-<rev>` | linux/amd64, linux/arm64 | `hosts/smartdash/` (the kiosk satellite) |

## Tags

- `openclaw` and `crispasr` derive their tag from the upstream version `ARG` in
  the Dockerfile (`OPENCLAW_VERSION`, `CRISPASR_VERSION`), so bumping the ARG
  and merging to `master` publishes a new tag. Reference that tag from home-ops.
- `oww-training` and `wakeword-capture` have no upstream version; they publish
  `latest` plus a `sha-<short>` tag for pinning a specific revision.

## Publishing

Push to `master` (or run the workflow from the Actions tab) publishes. Every
workflow also runs on `pull_request`, which **builds without pushing**, so an
image change is validated before it can reach a host.

Every Dockerfile carries
`LABEL org.opencontainers.image.source=https://github.com/lanquarden/container-images`,
which links the package to this repository so the GHCR package inherits its
public visibility. If a package is ever pushed for the first time without that
label, set its visibility to public by hand (Package settings → Change
visibility) or `podman pull` on a host will fail with `unauthorized`.

## Naming

Images are referenced by tag (`:latest`, `:<version>`), not digest, because the
consumers are hand-applied host definitions on `beast`/`smartdash`, not
Flux-reconciled cluster manifests. Pin a `sha-<rev>` tag where reproducibility
matters.
