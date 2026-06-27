# AUTOGENESIS — 30-second commercials

Two cinematic ads for the utility of this repo: **proof-carrying, verified robot
maintenance & replication**. Hand AUTOGENESIS a robot's *genome* and it returns
repair procedures that are inseparable from a tamper-evident certificate (the L3
verification layer) — nothing reaches an executor without a passing proof.

- `AUTOGENESIS_commercial_30s.mp4` — the core pitch (trust the fix). 1920×1080, 30.0s.
- `AUTOGENESIS_self_replication_30s.mp4` — robots building robots, robots maintaining
  themselves, and why security is non-negotiable once self-replication is real. 1920×1080, 30.0s.
- `AUTOGENESIS_swarm_30s.mp4` — a darker, warfare-framed cut: uncontrolled self-replication as
  a bottomless pit of steel locusts, bounded by the proof-gate. 1920×1080, 30.0s.
- `AUTOGENESIS_abundance_30s.mp4` — a bright, hopeful cut: autonomous systems ending scarcity and
  curing disease, made trustworthy by verifiable proof (safe by construction). 1920×1080, 30.0s.
- `AUTOGENESIS_for_all_30s.mp4` — an op-ed-style provocation: the capability to feed, house, and
  heal everyone exists, so why isn't it pointed at the public good? A call for auditable autonomy. 1920×1080, 30.0s.

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

## Storyboard / script — `AUTOGENESIS_self_replication_30s.mp4`

| # | Scene | Voiceover |
|---|-------|-----------|
| 1 | Assembly arms building a new humanoid robot on a line | "Soon, robots will build other robots." |
| 2 | A robot repairing its own open forearm panel | "And repair themselves. No human in the loop." |
| 3 | A branching lineage of robot copies; one distant red glitch spreading | "But every copy can inherit a flaw. One tampered procedure, spreading across an entire machine lineage." |
| 4 | A rogue robot with corrupted red code; a padlock shatters | "When machines replicate, security isn't optional." |
| 5 | A verification gateway passing green-sealed packets, rejecting a red one | "AUTOGENESIS makes proof the price of propagation. No certificate, no replication. Verified before it ever spreads." |
| 6 | Verified robots building & repairing each other; AUTOGENESIS logo | "Self-building. Self-healing. Provably secure. AUTOGENESIS." |

## Storyboard / script — `AUTOGENESIS_swarm_30s.mp4`

| # | Scene | Voiceover |
|---|-------|-----------|
| 1 | War-torn city, a swarm of military robots rising from the rubble | "This is self-replication without control. Machines that build machines." |
| 2 | A bottomless molten foundry-pit spawning machines like locusts | "One becomes two. Two become four. A swarm with no end." |
| 3 | An immense drone swarm blackening the sky | "A bottomless pit of steel locusts, darkening the sky. No army could stop it." |
| 4 | A fractal chain of robots replicating, red UNVERIFIED glyphs multiplying | "Unless every copy must first prove itself." |
| 5 | The swarm halts at a blazing verification gate; uncertified units power down | "AUTOGENESIS makes proof the price of replication. No certificate, no offspring." |
| 6 | Smoke clears over an orderly verified formation; AUTOGENESIS logo | "The swarm, bounded. AUTOGENESIS." |

## Storyboard / script — `AUTOGENESIS_abundance_30s.mp4`

| # | Scene | Voiceover |
|---|-------|-----------|
| 1 | Sunrise over a green city; autonomous systems working among people | "Imagine machines that never tire." |
| 2 | An autonomous vertical farm overflowing with fresh produce | "Autonomous systems that grow our food, build our cities, and end scarcity." |
| 3 | A biomedical lab designing a cure; a recovered patient smiles | "Tireless labs that hunt down disease and design the cure overnight. Abundance, and health, for everyone." |
| 4 | A certificate seal protecting a network of autonomous systems | "But autonomy you can't trust is a risk you can't take." |
| 5 | Actions flowing through a verification gate, each proof-sealed | "AUTOGENESIS gives every autonomous system a proof you can verify. Safe by construction." |
| 6 | A thriving green city of healthy people + verified robots; logo | "Abundance. Health. AUTOGENESIS." |

## Storyboard / script — `AUTOGENESIS_for_all_30s.mp4`

> An intentionally rhetorical / aspirational public-interest piece (a question, not a factual claim).

| # | Scene | Voiceover |
|---|-------|-----------|
| 1 | A colossal autonomous AI factory building through the night | "We already have the machines. Fully autonomous factories that build around the clock." |
| 2 | The same factory behind a locked gate, faded flag, dormant | "Enough capacity to feed, house, and heal everyone." |
| 3 | A split shot: humming machines vs. empty shelves and people in need | "So here's the question. Why isn't all that power pointed at the good of all of us?" |
| 4 | A lone official before a control panel, a question mark overhead | "The capability is real. The will... is missing." |
| 5 | The factory redirected to public good, output proof-sealed | "Imagine autonomy we can audit. Production we can trust." |
| 6 | Sunrise over thriving communities; AUTOGENESIS logo | "Turn the machines toward everyone. AUTOGENESIS." |
