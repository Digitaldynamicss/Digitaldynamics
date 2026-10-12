# Drop-in assets

Every file here is optional. When one is present, `render.py` uses it in place of
the built-in graphic. Supplied assets are the source of truth, so use official Honda
and dealership material only.

| File | Used in | Notes |
|---|---|---|
| `hero_bike.png` | Scene 1 hero roll-out | Transparent PNG cut-out, side profile facing **right** |
| `shine_dlx.png` | Scene 2 left column + end card | Official Honda Shine DLX cut-out, facing **right** |
| `cb125_hornet.png` | Scene 2 right column + end card | Official Honda CB125 Hornet cut-out, facing **right** (it is mirrored automatically to face the centre) |
| `showroom.jpg` | Scene 1 background + end-card background | Real Auto Scan Honda showroom photo, portrait or landscape |
| `gift_handover.jpg` | Scene 3 gift moment background | Representative handing a gift box to a customer |
| `logo.png` | Top brand bug (scenes 1–2) | Dealership logo, transparent PNG |
| `audio/voiceover.wav` | Whole reel | One 15 s take already timed to the scene table in `reel/README.md` |
| `audio/vo1.wav` … `audio/vo3b.wav` | Per line | Individual lines. Each is trimmed of silence and fitted into its slot |
| `audio/music.wav` | Whole reel | Licensed music track (≥15 s). Replaces the synthesised track and is still ducked under the VO |

Cut-outs: remove the background first (Canva / Photoshop / remove.bg), export as PNG
at roughly 2000 px wide, and crop tight to the motorcycle.
