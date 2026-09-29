# linux-voice-assistant

Builds and publishes the **Linux Voice Assistant** image consumed by
[`lanquarden/home-ops`](https://github.com/lanquarden/home-ops)
`hosts/smartdash/` — the smartdash wall-kiosk satellite (Raspberry Pi 4, arm64).

## Why this lives here

The upstream project
([`OHF-Voice/linux-voice-assistant`](https://github.com/OHF-Voice/linux-voice-assistant))
publishes `ghcr.io/ohf-voice/linux-voice-assistant`. Issue **#356** needs a
local change (bounded speech gain + external duck leases) that is not upstream,
so home-ops must not build it on a host (the rule in the top-level README).
Instead the change is implemented on a branch of a **fork** and this repository
builds and publishes the resulting image, exactly like `openclaw/`,
`crispasr/`, `oww-training/` and `wakeword-capture/`.

## Source pin

| Item | Value |
| --- | --- |
| Fork | `manolo-mistalibio/linux-voice-assistant` |
| Branch | `feat/356-bounded-speech-external-duck` |
| Pinned commit | see `LVA_REF` in `.github/workflows/linux-voice-assistant.yaml` |
| Base release | upstream `v1.1.15` (matches the currently deployed image) |
| Published as | `ghcr.io/lanquarden/linux-voice-assistant:<version>` and `:sha-<rev>` |

The workflow checks out the **fork at the pinned commit** and builds the
upstream `Dockerfile` unmodified, so the overlay is not a separate build
recipe: it is a source patch.

## Adopting a new revision

1. Merge/commit the change on the fork branch.
2. Update `LVA_REF` in `.github/workflows/linux-voice-assistant.yaml` and
   `LVA_VERSION` if the image tag should change.
3. Merge to `master`; the workflow publishes `:sha-<rev>` and `:<version>`.
4. Pin the new tag in home-ops `hosts/smartdash/.env` (`LVA_IMAGE`).

## Rollback

Point home-ops `LVA_IMAGE` back at the upstream pinned digest (documented in
`hosts/smartdash/README.md`); no image needs to be unpublished.
