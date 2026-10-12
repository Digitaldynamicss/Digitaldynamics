# Auto Scan Honda — 15 s Offer Reel

A 1080×1920, 30 fps, 15.000 s vertical reel for Instagram Reels, Facebook Reels and Meta Ads.
It is rendered programmatically with Python (Pillow + NumPy) and FFmpeg, with no paid
services or API keys.

**Output:** `reel/output/auto_scan_honda_reel_15s.mp4` (H.264 High, yuv420p, AAC 48 kHz stereo, -14 LUFS)

| File in `reel/output/` | What it is |
|---|---|
| `auto_scan_honda_reel_15s.mp4` | Final reel with burned-in Hinglish captions |
| `auto_scan_honda_reel_15s.srt` | Caption sidecar, for upload as Meta captions or for a version without burned-in captions |
| `auto_scan_honda_reel_15s_mix.wav` | Final audio mix |
| `auto_scan_honda_reel_15s_mix_music_only.wav` | Music bed only, for a voice artist to record against |
| `auto_scan_honda_reel_15s_contact_sheet.jpg` | 12 key frames for quick review |

## Read this before publishing

1. **The motorcycles are illustrations.** No dealership photos, logo or official Honda
   model images were supplied, and none were in the repository. The bikes are generic
   graphics with no badges or logos, so they don't misrepresent a model. Before the ad
   runs, drop official cut-outs of the **Shine DLX** and **CB125 Hornet**, plus a real
   showroom photo, into `reel/assets/` (see `assets/README.md`) and re-render. The
   layout adapts on its own.
2. **The voiceover is a robotic guide track** (offline `espeak-ng` Hindi). Natural
   neural TTS services were unreachable from the build environment. The guide gets the
   timing right, but it is **not broadcast quality**. Replace it with a recorded voice
   (workflow below).
3. **The scene 3 script is long for its slot.** "Abhi call ya WhatsApp karein
   9546036233. Auto Scan Honda, Munger." takes about 5–6 s at natural pace, but the
   slot is 3.9 s (11.05–14.95). The guide track plays it at about 1.6× speed. The voice
   artist should read it briskly. If that is not possible, consider trimming the line
   (for example by dropping "Abhi"). The on-screen copy is unaffected either way.
4. Offers are reproduced exactly as supplied: ₹4,999 down payment, ₹2,100 off the Shine
   DLX, ₹4,000 off the CB125 Hornet, assured gift, 9546036233, "T&C APPLY",
   "Finance subject to bank approval." Nothing else (EMI, interest, exchange, cashback,
   eligibility) appears anywhere.

## Render

```bash
# one-time: Python 3.10+, FFmpeg with libx264, Inter fonts, espeak-ng (guide VO only)
sudo apt-get install -y ffmpeg fonts-inter espeak-ng
pip install pillow numpy scipy        # scipy is optional (faster audio filters)

python3 reel/render.py                       # full render (~2 min)
python3 reel/render.py --still 1.5 8.2 13    # preview single frames -> reel/output/still_*.png
python3 reel/render.py --no-audio            # visuals only
```

To preview, open the MP4 in any player, or send it to a phone and watch it full screen.
That is the best check for legibility.

## Editing

All copy, offers, the phone number, colours and timings live in **`reel/config.json`**.
Change them there and re-render. The code is split into:

- `lib/scenes.py`: the three scenes (`scene_hook`, `scene_models` with a reusable
  `column()` component, `scene_cta`, `end_card`), the transitions and the caption layer.
  `Reel.frame(t)` is a pure function of time.
- `lib/gfx.py`: text, easing and compositing helpers, backgrounds, and the bike illustrations.
- `lib/audio.py`: the synthesised 120 BPM music, the voiceover assembly, ducking and
  loudness normalisation.

## Scene timing and script

| Time | Scene | On screen | Voiceover (Hinglish) |
|---|---|---|---|
| 0.0–3.0 | **Price hook.** The bike rolls out of the lit showroom gate in a low-angle push-in. ₹4,999 pops in on a red slab at 0.2 s, then gets a light sweep. | SIRF **₹4,999** DOWN PAYMENT MEIN HONDA GHAR! | *Sirf chaar hazaar nau sau ninyanve rupaye down payment mein Honda ghar laayein!* (0.10–3.05) |
| 2.7–3.3 | Red diagonal wipe | | |
| 3.0–6.3 | **Shine DLX** solo, warm "home" setting | GHAR KE LIYE · HONDA SHINE DLX · **₹2,100 KI CHHOOT** (amount from 3.9 s) | *Ghar ke liye Shine DLX par do hazaar ek sau rupaye ki chhoot.* (3.25–6.45) |
| 6.25–6.8 | Slanted split-screen: Shine moves left, Hornet's urban scene wipes in from the right | | |
| 6.5–10.0 | **CB125 Hornet** on the right, Shine kept on the left. Both offers are on screen together for the last 2.7 s. | STYLE KE LIYE · HONDA CB125 HORNET · **₹4,000 KI CHHOOT** (amount from 7.3 s) | *Style ke liye CB125 Hornet par chaar hazaar rupaye ki chhoot.* (6.60–9.85) |
| 9.8–10.25 | Red flash and zoom | | |
| 10.0–11.2 | **Assured gift.** A gift box bursts in over rotating light rays. | ASSURED GIFT 🎁 | *Saath mein assured gift!* (10.02–11.00) |
| 11.2–15.0 | **End card** (slides up, held to the last frame) | 🎁 ASSURED GIFT · CALL / WHATSAPP NOW (green) · **9546036233** (largest element) · AUTO SCAN HONDA · MUNGER · T&C APPLY · Finance subject to bank approval. | *Abhi call ya WhatsApp karein 9546036233. Auto Scan Honda, Munger.* (11.05–14.95) |

Captions are burned in at y≈1440, the band above the Reels bottom UI. All critical
content sits between y≈180 and y≈1500. The music is a 120 BPM instrumental with
impacts on every scene change, ducked by 11 dB under the voice. The final chord lands
at 14.0 s.

## Replacing the voiceover

1. Record against `output/auto_scan_honda_reel_15s_mix_music_only.wav` (or just the
   timings above). Use a confident, conversational Hindi male or female voice, and
   pronounce the number digit by digit.
2. Do one of the following:
   - Export one 15 s take aligned to the video as `reel/assets/audio/voiceover.wav`.
   - Export each line as `reel/assets/audio/vo1.wav`, `vo2a.wav`, `vo2b.wav`, `vo3a.wav`
     and `vo3b.wav`. Each line is trimmed of silence and fitted, pitch-preserved, into its slot.
3. Run `python3 reel/render.py`. Music ducking and loudness normalisation are reapplied.

To use AI voice services such as ElevenLabs (Hindi), Azure TTS (`hi-IN-MadhurNeural` /
`hi-IN-SwaraNeural`) or Google Cloud TTS: generate the five lines from the `subtitle`
text in `config.json` and save them as the per-line files above. A licensed music
track can be dropped in as `reel/assets/audio/music.wav`.

## Validation (last render)

Checked with `ffprobe` and `ebur128`:

- Duration: 15.000 s, 450 frames at 30 fps
- Video: H.264 High, 1080×1920, yuv420p, `+faststart`
- Audio: AAC 48 kHz stereo, integrated loudness ≈ -14.5 LUFS
- During every line, the voice is about 7–9 dB above the ducked music
- The phone number, all three amounts and both disclaimers were checked by eye on the
  contact sheet and on full-resolution stills
