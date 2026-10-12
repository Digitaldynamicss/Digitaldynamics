"""Soundtrack: synthesised 120 BPM instrumental + voiceover, mixed with ducking.

Voiceover source priority (first found wins):
  1. assets/audio/voiceover.wav       – one 15 s take already timed to the reel
  2. assets/audio/<id>.wav            – one file per line (vo1, vo2a, vo2b, vo3a, vo3b),
                                        each placed at its config start time and fitted to its slot
  3. espeak-ng Hindi guide voice      – offline placeholder so timing can be reviewed
Music: assets/audio/music.wav replaces the synthesised track if present."""
import os
import shutil
import subprocess
import tempfile

import numpy as np

SR = 48000
ASSET_AUDIO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")


def _read(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def write_wav(path, x, sr=SR):
    stereo = np.repeat(np.clip(x, -1, 1)[:, None], 2, axis=1) if x.ndim == 1 else x
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(sr), "-i", "-",
                    "-c:a", "pcm_s16le", path], input=stereo.astype(np.float32).tobytes(), check=True)


def db(x):
    return 10 ** (x / 20)


# ------------------------------------------------------------------ music

def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


def _lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):  # small buffers only
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def _onepole_fast(x, cutoff):
    from scipy.signal import lfilter  # optional speed-up
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def lp(x, cutoff):
    try:
        return _onepole_fast(x, cutoff)
    except ImportError:
        return _lowpass(x, cutoff)


def hp(x, cutoff):
    return x - lp(x, cutoff)


def _saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0, detune):
        f = freq * (1 + d)
        out += 2 * ((t * f) % 1) - 1
    return out / 3


def synth_music(duration, bpm=120, seed=3):
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    mix = np.zeros(n)
    beat = 60 / bpm
    sixteenth = beat / 4

    def add(sig, at, gain=1.0):
        i = int(at * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        mix[i:j] += sig[: j - i] * gain

    # kick: pitch-swept sine on every beat
    kn = int(0.32 * SR)
    t = np.arange(kn) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    kick += 0.3 * rng.normal(0, 1, kn) * np.exp(-t / 0.004)
    # clap: layered noise bursts
    cn = int(0.25 * SR)
    clap = np.zeros(cn)
    for off in (0, 0.009, 0.018):
        k = int(off * SR)
        burst = rng.normal(0, 1, cn - k) * _env(cn - k, 0.001, 0.05 if off == 0.018 else 0.008)
        clap[k:] += burst
    clap = hp(clap, 900)
    hat = hp(rng.normal(0, 1, int(0.06 * SR)), 7000) * _env(int(0.06 * SR), 0.0005, 0.018)
    open_hat = hp(rng.normal(0, 1, int(0.2 * SR)), 6000) * _env(int(0.2 * SR), 0.001, 0.07)

    beats = int(duration / beat)
    sidechain = np.ones(n)
    for b in range(beats):
        at = b * beat
        if at > duration - 0.6:  # leave the final chord ringing
            break
        add(kick, at, 0.95)
        i = int(at * SR)
        m = min(n - i, int(0.22 * SR))
        sidechain[i:i + m] = np.minimum(sidechain[i:i + m], 0.35 + 0.65 * (np.arange(m) / m))
        if b % 2 == 1:
            add(clap, at, 0.45)
        add(open_hat, at + beat / 2, 0.16)
        for s in (1, 3):
            add(hat, at + s * sixteenth, 0.14)

    # harmony: Am - F - C - G, one chord per bar (2 s)
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    roots = [45, 41, 48, 43]
    bar = beat * 4
    bass = np.zeros(n)
    pluck = np.zeros(n)
    pad = np.zeros(n)
    for bi in range(int(np.ceil(duration / bar))):
        ch = chords[bi % 4]
        root = roots[bi % 4]
        t0 = bi * bar
        # driving 8th-note bass
        for e in range(8):
            at = t0 + e * beat / 2
            ln = int(beat / 2 * SR)
            i = int(at * SR)
            if i >= n:
                break
            f = 440 * 2 ** ((root - 12 - 69) / 12) * (2 if e % 4 == 3 else 1)
            sig = (_saw(f, ln, 0.004) * 0.6 + np.sin(2 * np.pi * f * np.arange(ln) / SR)) * _env(ln, 0.003, 0.18)
            j = min(n, i + ln)
            bass[i:j] += sig[: j - i]
        # 16th-note arpeggio
        seq = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[1], ch[2] + 12]
        for k in range(16):
            at = t0 + k * sixteenth
            i = int(at * SR)
            if i >= n:
                break
            ln = int(0.22 * SR)
            f = 440 * 2 ** ((seq[k % 8] + 12 - 69) / 12)
            sig = _saw(f, ln, 0.006) * _env(ln, 0.002, 0.07)
            j = min(n, i + ln)
            pluck[i:j] += sig[: j - i]
        # pad
        i, j = int(t0 * SR), min(n, int((t0 + bar) * SR))
        ln = j - i
        if ln > 0:
            for note in ch:
                pad[i:j] += _saw(440 * 2 ** ((note - 69) / 12), ln, 0.01) * 0.33
    bass = lp(bass, 380)
    pluck = lp(pluck, 3200)
    delayed = np.zeros(n)
    dly = int(beat * 0.75 * SR)
    delayed[dly:] = pluck[:-dly] * 0.35
    pluck = pluck + delayed
    pad = lp(pad, 1400)
    mix += sidechain * (bass * 0.42 + pluck * 0.13 + pad * 0.10)

    # risers + impacts on scene changes
    def riser(start, end, gain):
        i, j = int(start * SR), int(end * SR)
        ln = j - i
        x = rng.normal(0, 1, ln)
        ramp = np.linspace(0, 1, ln) ** 2
        x = hp(x, 1500) * ramp
        mix[i:j] += x * gain

    def impact(at, gain):
        ln = int(1.2 * SR)
        t = np.arange(ln) / SR
        boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.45)
        crash = hp(rng.normal(0, 1, ln), 3000) * np.exp(-t / 0.35) * 0.35
        add(boom + crash, at, gain)

    riser(2.0, 3.0, 0.10)
    riser(9.0, 10.0, 0.10)
    for at in (0.0, 3.0, 10.0):
        impact(at, 0.55)
    impact(11.2, 0.35)
    # closing chord hit at 14.0 that rings to the end
    end_at = 14.0
    i = int(end_at * SR)
    ln = n - i
    hit = np.zeros(ln)
    for note in (45, 57, 60, 64, 69):
        hit += _saw(440 * 2 ** ((note - 69) / 12), ln, 0.008)
    hit = lp(hit, 2200) * _env(ln, 0.003, 0.5) * 0.35
    mix[i:] += hit
    impact(end_at, 0.5)

    mix = np.tanh(mix * 1.1)
    fade = int(0.08 * SR)
    mix[:fade] *= np.linspace(0.6, 1, fade)
    mix[-int(0.25 * SR):] *= np.linspace(1, 0, int(0.25 * SR))
    return mix / (np.max(np.abs(mix)) + 1e-9) * 0.9


# ------------------------------------------------------------------ voiceover

def _atempo_chain(factor):
    parts = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        parts.append("atempo=0.5")
        factor /= 0.5
    parts.append(f"atempo={factor:.4f}")
    return ",".join(parts)


def _trim_silence(path_in, path_out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path_in, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", str(SR), "-ac", "1", path_out], check=True)


def _fit(path_in, slot, tmp):
    """Return mono samples of a VO line time-stretched (pitch-preserving) to fit `slot` seconds."""
    trimmed = os.path.join(tmp, os.path.basename(path_in) + ".trim.wav")
    _trim_silence(path_in, trimmed)
    x = _read(trimmed)
    dur = len(x) / SR
    factor = dur / slot
    if factor > 1.0 or factor < 0.85:
        factor = max(factor, 0.92) if factor < 1 else factor
        out = os.path.join(tmp, os.path.basename(path_in) + ".fit.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", trimmed, "-af", _atempo_chain(factor), out], check=True)
        x = _read(out)
    return x[: int(slot * SR)], dur, factor


def _tts(line, path, rate=175):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("No voiceover supplied and espeak-ng is not installed (apt-get install espeak-ng).")
    subprocess.run([exe, "-v", "hi+m3", "-s", str(rate), "-p", "42", "-a", "180", "-w", path, line], check=True)


def build_voiceover(cfg, tmp, log):
    n = int(cfg["video"]["duration"] * SR)
    full = os.path.join(ASSET_AUDIO, "voiceover.wav")
    if os.path.exists(full):
        x = _read(full)[:n]
        log.append(("voiceover", "supplied single take assets/audio/voiceover.wav"))
        return np.pad(x, (0, n - len(x))), "supplied"
    vo = np.zeros(n)
    source = "supplied"
    for line in cfg["voiceover"]:
        supplied = os.path.join(ASSET_AUDIO, f'{line["id"]}.wav')
        if os.path.exists(supplied):
            src = supplied
        else:
            src = os.path.join(tmp, f'{line["id"]}.tts.wav')
            _tts(line["tts"], src)
            source = "espeak-ng guide"
        slot = line["end"] - line["start"]
        x, natural, factor = _fit(src, slot, tmp)
        x = hp(x, 90)
        i = int(line["start"] * SR)
        j = min(n, i + len(x))
        vo[i:j] += x[: j - i]
        log.append((line["id"], f"{os.path.basename(src)}: natural {natural:.2f}s -> slot {slot:.2f}s (tempo x{factor:.2f})"))
    vo = vo / (np.max(np.abs(vo)) + 1e-9) * 0.95
    return vo, source


def build_soundtrack(cfg, out_path, log):
    a = cfg["audio"]
    n = int(cfg["video"]["duration"] * SR)
    with tempfile.TemporaryDirectory() as tmp:
        vo, source = build_voiceover(cfg, tmp, log)
        music_file = os.path.join(ASSET_AUDIO, "music.wav")
        if os.path.exists(music_file):
            music = _read(music_file)[:n]
            music = np.pad(music, (0, n - len(music)))
            log.append(("music", "supplied assets/audio/music.wav"))
        else:
            music = synth_music(cfg["video"]["duration"], a["music_bpm"])
            log.append(("music", f'synthesised {a["music_bpm"]} BPM instrumental'))
        # ducking: smooth VO envelope drives music gain down by duck_db
        env = lp(np.abs(vo), 8)
        env = np.clip(env / (np.max(env) + 1e-9) * 4, 0, 1)
        env = lp(env, 6)
        gain = db(a["music_gain_db"]) * (1 - (1 - db(a["duck_db"])) * env)
        mix = music * gain + vo
        raw = os.path.join(tmp, "mix.wav")
        write_wav(raw, mix / (np.max(np.abs(mix)) + 1e-9) * 0.8)
        # loudness-normalise for social platforms
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                        f'loudnorm=I={a["target_lufs"]}:TP=-1.5:LRA=9', "-ar", str(SR), "-t", str(cfg["video"]["duration"]),
                        out_path], check=True)
        write_wav(out_path.replace(".wav", "_music_only.wav"), music * db(a["music_gain_db"]))
    return source
