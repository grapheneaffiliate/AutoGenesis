# AUTOGENESIS — 30-second commercial

`AUTOGENESIS_commercial_30s.mp4` — 1920×1080, 30.0s, H.264 + AAC.

A cinematic ad for the utility of this repo: **proof-carrying, verified robot
maintenance & replication**. Hand AUTOGENESIS a robot's *genome* and it returns
repair procedures that are inseparable from a tamper-evident certificate (the L3
verification layer) — nothing reaches an executor without a passing proof.

## How it was made (Higgsfield)

- **Stills** — 6 storyboard frames, `nano_banana_pro`, 16:9, 2K.
- **Motion** — each still animated to a 5s clip, `seedance_2_0`, 1080p (silent).
- **Voiceover** — `text2speech_v2_elevenlabs`, voice "Sterling".
- **Assembly** — `ffmpeg`: concat 6×5s → 30s, voiceover time-fit to the timeline,
  loudness-normalized, with fade in/out. Build steps in `../../scratchpad_video/build.sh`.

## Storyboard / script

| # | Scene | Voiceover |
|---|-------|-----------|
| 1 | Industrial robot failing in a dark factory, red warning light | "Every robot eventually breaks down. The real question — can you trust the fix?" |
| 2 | Technician under red alerts; a fleet powers down one by one | "One wrong part. One unverified torque. And failure spreads across your entire fleet." |
| 3 | Holographic robot *genome* blueprint rotating | "AUTOGENESIS changes that. Feed it a robot's genome..." |
| 4 | A proof certificate materializing with check marks & a seal | "...and it returns repair procedures that carry their own mathematical proof." |
| 5 | Verified repair inside a green safety-envelope hologram | "Spec. Feasibility. Safety. Every step verified, before it ever reaches a machine." |
| 6 | A fleet powers on in unison; AUTOGENESIS logo | "AUTOGENESIS. Proof-carrying maintenance. Self-replication, made safe." |
