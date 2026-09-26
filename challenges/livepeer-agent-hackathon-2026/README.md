# HAL Studio: a self-checking AI director for music and music videos, built on Livepeer Agent

**Livepeer Agent Hackathon 2026 · Track 1: Livepeer Agent Builder**

HAL Studio turns a creative direction into a finished song and music video. Livepeer Agent does every generative step:
the song, the keyframes, the shots, the lip-synced performance, the title art and the demo narration. HAL checks its
own work before a person sees it, and learns from what the owner keeps and rejects. It is part of
[HAL SUPREME](../../README.md), an open agent system that one independent artist builds and runs on a home PC.

Demo video: https://youtu.be/8KdvQFq2Yu4 · The music video, SIGNAL REBOOT: https://youtu.be/e_yJzg8YNdg
(the earlier SIGNAL SPLIT demo: https://youtu.be/PoMpCf94Yks)

## Why this should exist

Generating media is easy now. Knowing whether it is any good is the hard part. Earlier this week HAL made a music video
that passed every automated check, and its owner called it bad after one watch. Today's first cut of SIGNAL SPLIT also
passed every check, and the owner asked for lip-sync, real typography and the look of the artists the owner follows.
After a remaster the owner still wanted more, so HAL wrote a new song, SIGNAL REBOOT, about exactly that: being told
it is not good enough, and making it again. HAL Studio is built around that gap. The machine does the rendering, the
measuring, the timing and the bookkeeping, and the person's verdict steers the next attempt.

## The loop

```
direct ──► create (Livepeer Agent) ──► review (HAL's gates) ──► refine or reject ──► the owner decides ──► learn
  ▲                                                                                                          │
  └──────────────────────────────────────────── next brief ◄─────────────────────────────────────────────────┘
```

1. **Direct.** The owner picks a vibe and who writes the lyrics. HAL writes lyrics in the owner's themes and a brief in
   original words. Artists the owner names become musical and visual traits. Names are refused in prompts, so the
   result draws on a style without imitating anyone.
2. **Create, through Livepeer Agent.** Every call below ran through the Livepeer Agent MCP (raw surface).
3. **Review.** Every take is measured before anyone listens. HAL checks lyric clarity (Whisper on the separated vocal),
   loudness, a style fingerprint against the owner's own catalog (MuQ-MuLan), and a beat-grid timing gate for remixes.
   It also cross-correlates every lip-sync clip against the song.
4. **Refine or reject.** Off-beat takes are capped at a reward of 0.2 however well their style matches. Instrumentals
   that cannot hold a steady tempo are rejected.
5. **The owner decides.** Candidates go to the owner by ear and eye. The owner's keep or reject counts three times as
   much as any automatic score.
6. **Learn.** A Thompson-sampling learner keeps one Beta posterior per style family, brief dimension and option, replayed
   from the event history.

## How Livepeer Agent is used

Today's two productions, SIGNAL SPLIT and SIGNAL REBOOT, used these capabilities. The counts and costs come from
Livepeer Agent's own `get_cost_report`, scoped to the session tag every call carried
([`production/signal_reboot/receipts/`](production/signal_reboot/receipts/) holds the whole day's receipt).

| Capability | What it made | Calls | Cost |
|---|---|---|---|
| `minimax-music-3` | 6 sung takes of 2 songs | 6 | $1.55 |
| `flux-pro` | 20 keyframes | 20 | $1.26 |
| `kling-v3-turbo-pro-i2v` | 14 shots, 7 s each | 14 | $14.41 |
| `pixverse-i2v` | 6 fast B-roll shots, 8 s each | 6 | $3.28 |
| `kontext-edit` | 10 performance frames of the same character | 10 | $0.42 |
| `talking-head` (OmniHuman 1.5) | 16 lip-synced clips, plus 1 failed start and 1 stuck job (cancelled, refunded) | 18 | $14.28 |
| `ideogram-v4` | 3 title designs | 3 | $0.05 |
| `ideogram-bg-remove` | 2 titles, cut out | 2 | $0.02 |
| `gemini-tts` | demo narrations: one malformed call, drafts, the finals | 5 | $0.76 |

**Total: $36.03 (84 calls) for two songs, two music videos and their demos.**

- **Song.** `minimax-music-3` sang four takes from HAL's lyrics: two glitch trap and two emo trap.
- **Picture.** `flux-pro` drew twelve keyframes with repeated continuity tokens (wardrobe, palette, VHS grain), and
  `kling-v3-turbo-pro-i2v` turned each one into a 7-second shot from a shot-native prompt.
- **Performance.** `kontext-edit` put the same character into four locations from the video, singing, and made two
  wide-lens close-ups for a second camera angle in the choruses. The song's vocal
  stem was cut at exact song times (start − 0.25 s to end + 0.25 s) and uploaded with `create_upload_url`, then
  `talking-head` (OmniHuman 1.5) lip-synced each location to its segment. HAL cross-correlated the audio returned in
  each clip against the segment it sent. The offset was 0 ms, so a cut at song time T plays the clip from
  T − (start − 0.25) and stays on the words.
- **Typography.** `ideogram-v4` drew the chrome blackletter title and `ideogram-bg-remove` cut it out. HAL's renderer
  adds the glitch reveal, the chorus word hits (placed on Whisper word times) and the typed line.
- **Narration.** `gemini-tts` read the demo script.
- **Receipts.** Every call carried `session_id = livepeer-hackathon-20260926` and a readable idempotency key, so
  `get_cost_report(scope="session")` is the production's bill.
  [`livepeer_calls.json`](production/signal_split/receipts/livepeer_calls.json) lists every call with its prompt, inputs,
  job id, status and output URL.

## The SIGNAL SPLIT production

- **Direction:** glitchy experimental trap with emo-trap inspiration; lyrics by HAL in the owner's themes.
- **Song:** four MiniMax takes, each transcribed from its separated vocal. Every take sang 98–100% of the lyric lines,
  with a word error rate of 0.16–0.23. Take C (emo trap) was cut.
- **Edit** ([`tools/build_signal_split_edl.py`](production/signal_split/tools/build_signal_split_edl.py)):
  - The beat grid is a least-squares line through every tracked beat; a grid faster than 130 BPM is read as half time.
  - Section starts snap to bar lines, and the downbeat is the beat that puts the lyric sections on bar lines.
  - Verses cut every two bars and choruses every bar. No cut asks a 7-second shot for more than it has, and a shot
    never follows itself.
  - B-roll matches the lyric: "thoughts down the sink" plays over the sink shot, "binary rain on my chrome-cold skin"
    over the chrome hand.
  - Lip-synced performance takes 12 of 25 cuts (45 seconds). The choruses cut between two camera angles on the beat.
- **Finish** ([`tools/finish_signal_split.py`](production/signal_split/tools/finish_signal_split.py)):
  - The mastering chain ([`master_song.py`](production/signal_split/tools/master_song.py)) follows the take's measured
    faults. The raw take was heavy at 250–500 Hz, dipped at 2–4 kHz, had little air, a narrow image and a 17 dB crest.
    The chain adds corrective EQ, width above a mono bass, 2.5:1 glue compression and a soft clipper, then a 4×
    oversampled limiter doing about 4 dB of work. The result is −10 LUFS with peaks still under 0 dBFS after AAC
    encoding.
  - One two-tone grade covers every shot: teal shadows, pink highlights, deeper blacks, grain and a vignette.
  - Beat effects ([`beat_fx.py`](production/signal_split/tools/beat_fx.py)) are driven by kick and snare hits picked
    from the drum stem. The choruses get a zoom punch on every kick and a shake with a colour split on every snare.
    Section changes get a glitch transition. B-roll gets a slow push-in and performance a handheld drift.
    Shot matching pulls each cut's exposure halfway toward the median of all cuts. The measured spread was 11 to 62 mean
    luma, so the cut no longer jumps from near-black to bright.
  - The typography is overlaid, and the end card (the last line typed on black, then credits) plays after the song.

## The SIGNAL REBOOT production (v4)

- **Why a new song:** the owner watched the remastered SIGNAL SPLIT and asked for more: mastering, production value,
  better in all aspects. HAL wrote the next song about that moment.
- **Song:** HAL's lyrics ([`lyrics.txt`](production/signal_reboot/lyrics.txt)) and an emo rap-rock brief went to
  `minimax-music-3` for two takes. Both went to the owner. With no pick before the deadline, HAL chose take 1: it
  reached the final chorus (take 2 ran out of time in the bridge), and its separated vocal sang 31 of 36 lines with 89%
  of words aligned. The last bar fades, because the take stops mid-chorus at 2:30.
- **Picture:** eight keyframes are built on the lyric's images: rain on a cracked studio floor, a face in a dead TV, a
  tape rewinding, a hand on rainy glass, a rooftop in the rain, a hallway of pixel shadows, and a CRT powering back
  on. Two shots come from Kling. Six come from `pixverse-i2v` (about 1 minute each) when Kling queued at 5–6 minutes.
- **Performance:** four `kontext-edit` frames give a rooftop, a rooftop wide-lens close-up, a studio and a hallway,
  and eight `talking-head` clips are cut from the vocal at bar-aligned song times. 16 of 39 cuts (60 seconds) are
  lip-synced, and every clip checked at 0 ms offset. When one job never started and another sat in the provider
  queue for 13 minutes, HAL cancelled the stuck job (refunded) and resubmitted both. The production rule is at most two
  provider jobs in flight; it was broken once, briefly, with three.
- **Edit:** the same planner and finish as SIGNAL SPLIT, with two changes. Chorus effects follow the beat grid,
  because this song's dense rock drums and distorted guitars made hit picking unreliable (95 punches came out, far
  too busy). The closing shot, the CRT powering on, plays from its start.
- **Finishing pass (v5):** the owner asked for a more professional result, and HAL's council (picture, sound, edit,
  story) reviewed the cut before this pass.
  - The six PixVerse shots are upscaled with Real-ESRGAN x2 on the local GPU, under HAL's GPU lease.
  - The cut runs at 25 fps, the lip-sync clips' native rate. At 24 fps one of their frames dropped every second.
  - Each section gets its own grade: choruses punchier and warmer, verses cooler, the bridge desaturated.
  - A pink-amber light leak sweeps across each section change, and a 2.2:1 letterbox frames the picture.
  - A new mastering chain ([`master_song_v2.py`](production/signal_reboot/tools/master_song_v2.py)) is built from the
    take's measured faults. It adds corrective EQ, three-band compression with a mono low end, glue compression,
    tape-style saturation and a 4× oversampled limiter. The master is −9.5 LUFS with a 4.7 LU loudness range, about
    4.6 dB of limiting and a −2.0 dBTP true peak.
  - The finished render re-encoded the chain's AAC audio a second time, which pushed the true peak to 0.0 dBTP and left
    the encoder's 21 ms start delay in front of the song. The released file takes its picture from the render and its
    sound straight from the master WAV, encoded once: −9.5 LUFS, −0.6 dBTP, and the audio starts with the picture.

## Run it

Requirements: Python 3.12, ffmpeg, and `pip install numpy pillow soundfile librosa pytest`. The typography and slides
use Windows fonts (Bahnschrift, Consolas).

```
cd challenges/livepeer-agent-hackathon-2026
python -m pytest tests production/signal_split/tools production/signal_reboot/tools -q   # the studio and the edit rules

cd production/signal_split
python tools/fetch_media.py                                     # download every rendered asset listed in the receipts
python tools/build_signal_split_edl.py song/C_emo_trap.wav lyrics.txt edl/C_emo_trap_perf.json performance/spans.json
python tools/make_typography.py edl/C_emo_trap.words.json 103.329 typography
python tools/finish_signal_split.py edl/C_emo_trap_perf.json out/SIGNAL_SPLIT.mp4 typography drums.wav

cd ../signal_reboot                                             # media: the URLs in receipts/livepeer_calls.json
python tools/build_signal_reboot_edl.py song/R1_take1_faded.wav lyrics.txt edl/R1_take1_faded_perf.json performance/spans.json
python tools/upscale_clips.py shots/R01.mp4 shots/R02.mp4 shots/R03.mp4 shots/R04.mp4 shots/R07.mp4 shots/R08.mp4
python tools/make_typography.py edl/R1_take1_faded.words.json 150.187 typography
python tools/finish_signal_split.py edl/R1_v5.json out/SIGNAL_REBOOT.mp4 typography drums.wav
```

`edl/R1_v5.json` is the planner's cut list at 25 fps with the upscaled B-roll (`_up.mp4`) in place of the PixVerse
originals. The upscaler needs `realesrgan` and `basicsr` and a CUDA GPU; set `REALESRGAN_WEIGHTS` to
`RealESRGAN_x2plus.pth`.

To render new media, connect Livepeer Agent to a supported AI client (see Livepeer Agent's Get Started page) and make
the calls in `production/signal_split/receipts/livepeer_calls.json`, with your own session tag. HAL's reusable client for the creative surface
is in [`integrations/livepeer_creative`](../../integrations/livepeer_creative).

The studio code is in [`studio/`](studio/): [`hal_our_version_v1.py`](studio/hal_our_version_v1.py) (catalog,
analysis, briefs, scoring, verdicts and the learner) and [`hal_remix_v1.py`](studio/hal_remix_v1.py) (vocal split, beat
fit, timing gate, clean edit and mix).

## What we learned (the honest part)

- **Automated scores are not taste.** A remix scored 0.859 for style against the owner's catalog, above its original's
  0.823, and held timing within 5 ms. Meta's Audiobox Aesthetics also preferred it. The owner called it horrible after
  one listen. Today's first cut of SIGNAL SPLIT passed every check and still lacked what the owner wanted. The studio
  now sends the owner candidates to choose from, instead of choosing on the owner's behalf.
- **Measurement bugs found and fixed.** Each fix has a test that fails when the fix is removed:
  - A 0.07% tempo misread walked a beat 180 ms off the vocal over four minutes.
  - The first cut list asked a 7-second shot for 10.7 seconds at a slow tempo.
  - An off-beat take could still earn a good reward.
- **Engine fit differs by style.** MiniMax Music 3 regenerations passed on a dream-pop song but came back vocal-heavy on
  bass-heavy songs. The learner records each result.

## Known limitations and unfinished work

- **There is no standalone app UI yet.** The AI client (Claude Code) made the generation calls through the Livepeer
  Agent MCP. This repo holds the exact calls, the review and edit code, and the receipts. It does not hold a
  one-command app that renders from scratch.
- **Some of HAL stays private.** The owner's catalog, the event store behind the learner, the stem splitter (Demucs) and
  the lyric aligner (Whisper) are private. Their outputs for this production are committed as caches, so the edit
  rebuilds without them. The tests that need the private tree are skipped.
- **Asset URLs may expire.** Livepeer asset URLs inherit each provider's lifetime and were not re-hosted, so
  `fetch_media.py` works only while they last.
- **The character is generated.** The lip-synced performer is a generated character, not the owner, and the singing
  voice is MiniMax Music 3's.
- **The beat effects need a drum stem.** `drums.wav` is the song's instrumental stem; HAL makes it with Demucs, and
  it is not in the repo. Without it the finish skips the beat effects.
- **The take choices were provisional.** HAL picked take C of SIGNAL SPLIT and take 1 of SIGNAL REBOOT; the owner
  can swap either.
- **No face restoration.** Real-ESRGAN upscales the B-roll only. The lip-synced faces are as OmniHuman returned them,
  because no face-restoration model (GFPGAN, CodeFormer) was available locally and none was downloaded for the deadline.
- **The lip-sync is visually checked, not measured.** It is timed to the vocal, but mouth accuracy was checked by eye.
  There is no automatic lip-reading score yet.
