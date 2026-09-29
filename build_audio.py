#!/usr/bin/env python3
"""Build morning pyramid workout audio tracks.

- Synthesizes a light background-music bed (3 variants) with numpy.
- Synthesizes pacing beeps (2.5s/rep per the brief).
- Splits bundled voice clips into individual cues by silence detection.
- Mixes voice + music (with ducking) + beeps into final MP3s.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "audio")
os.makedirs(OUT, exist_ok=True)

BPM = 104.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT


# ---------------------------------------------------------------- voice I/O
def decode_voice(path):
    """Decode any audio file to mono float64 @ SR."""
    cmd = [FF, "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", "-f", "f64le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float64).copy()


def envelope(x, win_ms=10.0):
    win = max(1, int(SR * win_ms / 1000))
    n = len(x) // win
    return np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1))


def split_by_silence(x, expect, min_gaps=(0.30, 0.22, 0.40, 0.16)):
    """Split a bundle clip into `expect` segments at silent gaps."""
    env = envelope(x)
    peak = env.max() + 1e-12
    for min_gap in min_gaps:
        thr = max(0.02 * peak, 1e-4)
        active = env > thr
        # find silent runs
        cuts, i, n = [], 0, len(active)
        while i < n:
            if not active[i]:
                j = i
                while j < n and not active[j]:
                    j += 1
                if (j - i) * 0.010 >= min_gap:
                    cuts.append((i + j) // 2 * int(SR * 0.010))
                i = j
            else:
                i += 1
        segs, prev = [], 0
        for c in cuts + [len(x)]:
            seg = x[prev:c]
            prev = c
            if len(seg) > int(0.15 * SR):
                segs.append(trim_silence(seg))
        if len(segs) == expect:
            return segs
    raise RuntimeError(f"split failed: got {len(segs)} segments, expected {expect}")


def split_at(x, cuts):
    """Split at explicit cut times (seconds), trim each segment."""
    pts = [0.0] + list(cuts) + [len(x) / SR]
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        seg = x[int(a * SR): int(b * SR)]
        segs.append(trim_silence(seg))
    return segs


def trim_silence(x, pad=0.05):
    env = envelope(x)
    thr = max(0.03 * env.max(), 1e-4)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    win = int(SR * 0.010)
    p = int(pad * SR)
    a = max(0, idx[0] * win - p)
    b = min(len(x), (idx[-1] + 1) * win + p)
    return x[a:b]


# ---------------------------------------------------------------- music bed
def _pan_place(L, R, sig, t0, gain, pan=0.5):
    i = int(t0 * SR)
    if i >= len(L):
        return
    j = min(len(L), i + len(sig))
    s = sig[: j - i] * gain
    l, r = np.cos(pan * np.pi / 2), np.sin(pan * np.pi / 2)
    L[i:j] += s * l * 1.414
    R[i:j] += s * r * 1.414


def _sine(f, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    return np.sin(2 * np.pi * f * t)


def _pad_sig(dur, f):
    t = np.arange(int(dur * SR)) / SR
    a, r = 0.30, 0.35
    env = np.minimum(np.minimum(t / a, (dur - t) / r), 1.0)
    env = np.clip(env, 0, 1)
    return np.sin(2 * np.pi * f * t) * env


def _pluck(f, dur=0.24):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 13.0) * np.clip(t / 0.004, 0, 1)
    return (_sine(f, dur) + 0.32 * _sine(2 * f, dur) + 0.12 * _sine(3 * f, dur)) * env


def _kick(gain_scale=1.0):
    dur = 0.14
    t = np.arange(int(dur * SR)) / SR
    f = 46 + 115 * np.exp(-t * 20)
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * np.exp(-t * 24) * gain_scale


def _shaker(dur=0.045):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(7).standard_normal(len(t))
    hp = np.diff(n, prepend=0.0)
    return hp * np.exp(-t * 85) * 0.7


CHORDS = [
    # (pad notes, bass, arp notes)
    ([130.81, 164.81, 196.00, 261.63, 329.63], 65.41, [261.63, 329.63, 392.00, 523.25]),   # C
    ([98.00, 123.47, 146.83, 196.00, 246.94], 98.00, [246.94, 293.66, 392.00, 493.88]),     # G
    ([110.00, 130.81, 164.81, 220.00, 261.63], 110.00, [261.63, 329.63, 440.00, 523.25]),   # Am
    ([87.31, 110.00, 130.81, 174.61, 220.00], 87.31, [261.63, 349.23, 440.00, 523.25]),     # F
]

VARIANTS = {
    "bright": dict(pad=0.050, bass=0.10, kick=0.14, kick_beats=(0, 2), shaker=0.030, arp=0.045, arp_div=8, peak=0.22),
    "calm":   dict(pad=0.060, bass=0.07, kick=0.0,  kick_beats=(),     shaker=0.012, arp=0.028, arp_div=4, peak=0.18),
    "steady": dict(pad=0.055, bass=0.09, kick=0.07, kick_beats=(0,),   shaker=0.018, arp=0.0,   arp_div=8, peak=0.20),
}


def render_music(dur, variant="bright"):
    v = VARIANTS[variant]
    n = int((dur + 0.5) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    kick_sig = _kick()
    shaker_sig = _shaker()
    t = 0.0
    bar_i = 0
    while t < dur + 0.2:
        pad_notes, bass_f, arp_notes = CHORDS[bar_i % 4]
        for f in pad_notes:
            _pan_place(L, R, _pad_sig(BAR, f), t, v["pad"] / len(pad_notes) * 2.2)
        for b in v["kick_beats"]:
            _pan_place(L, R, kick_sig, t + b * BEAT, v["kick"])
        _pan_place(L, R, _sine(bass_f, BEAT * 0.9) * np.exp(-np.arange(int(BEAT * 0.9 * SR)) / SR * 1.6), t, v["bass"])
        _pan_place(L, R, _sine(bass_f, BEAT * 0.7) * np.exp(-np.arange(int(BEAT * 0.7 * SR)) / SR * 1.8), t + 2 * BEAT, v["bass"] * 0.85)
        if v["shaker"] > 0:
            step = BEAT * 2 / v["arp_div"] if False else BEAT / 2
            for k in range(8):
                g = v["shaker"] * (1.15 if k % 2 == 1 else 0.8)
                _pan_place(L, R, shaker_sig, t + k * step, g, pan=0.35)
        if v["arp"] > 0:
            step = BEAT * 4 / v["arp_div"]
            for k in range(v["arp_div"]):
                f = arp_notes[k % len(arp_notes)]
                _pan_place(L, R, _pluck(f), t + k * step, v["arp"], pan=0.68 if k % 2 == 0 else 0.30)
        t += BAR
        bar_i += 1
    out = np.stack([L, R], axis=1)[: int(dur * SR)]
    peak = np.abs(out).max() + 1e-9
    return out / peak * v["peak"]


# ---------------------------------------------------------------- beeps
def beep(freqs=(880.0,), dur=0.065, decay=38.0):
    t = np.arange(int(dur * SR)) / SR
    s = sum(_sine(f, dur) for f in freqs) / len(freqs)
    return s * np.exp(-t * decay) * np.clip(t / 0.002, 0, 1)


BEEP = beep((880.0,), 0.065, 38.0)
ACCENT = beep((880.0, 1320.0), 0.11, 26.0)
CHIRP = np.concatenate([beep((1320.0,), 0.055, 30.0), np.zeros(int(0.05 * SR)), beep((1760.0,), 0.075, 26.0)])
TICK = beep((660.0,), 0.045, 45.0)


# ---------------------------------------------------------------- mixing
def build_track(duration, music_variant, voices, beeps_list, fade_out=2.5, fade_in=0.4):
    """voices: list of (t0, mono_array, gain). beeps_list: list of (t0, mono_array, gain)."""
    n = int(duration * SR)
    music = render_music(duration, music_variant)
    if len(music) < n:
        music = np.pad(music, ((0, n - len(music)), (0, 0)))
    music = music[:n]

    voice = np.zeros(n)
    for t0, sig, g in voices:
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        voice[i:j] += sig[: j - i] * g

    # duck music under voice (vectorized envelope follower)
    win = int(0.010 * SR)
    nv = n // win
    env = np.sqrt((np.abs(voice[: nv * win]).reshape(nv, win) ** 2).mean(axis=1))
    env = np.repeat(env, win)[:n]
    if n - len(env) > 0:
        env = np.pad(env, (0, n - len(env)))
    # smooth: fast attack (~8ms), slow release (~170ms) via asymmetric convolution approx
    klen = int(0.18 * SR) | 1
    t = np.arange(klen)
    kern = np.where(t < klen // 6, 1.0, np.exp(-(t - klen // 6) / (0.09 * SR)))
    kern /= kern.sum()
    sm = np.convolve(env, kern, mode="same")
    duck = np.clip(1.0 - 0.55 * np.clip(sm / 0.08, 0, 1), 0.35, 1.0)
    music = music * duck[:, None]

    master = music.copy()
    master[:, 0] += voice * 0.92
    master[:, 1] += voice * 0.92
    for t0, sig, g in beeps_list:
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        master[i:j, 0] += sig[: j - i] * g
        master[i:j, 1] += sig[: j - i] * g

    # fades
    fi = int(fade_in * SR)
    master[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(fade_out * SR)
    master[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5

    peak = np.abs(master).max()
    if peak > 0.93:
        master *= 0.93 / peak
    return np.clip(master, -1, 1)


def write_mp3(master, name, keep_wav=False):
    wav_path = os.path.join(RAW, name + ".wav")
    data = (master * 32767).astype(np.int16)
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    mp3_path = os.path.join(OUT, name + ".mp3")
    subprocess.run([FF, "-y", "-v", "error", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", "128k", mp3_path], check=True)
    if not keep_wav:
        os.remove(wav_path)
    return mp3_path, len(master) / SR


def read_wav_stereo(name):
    wav_path = os.path.join(RAW, name + ".wav")
    with wave.open(wav_path, "rb") as w:
        assert w.getnchannels() == 2 and w.getsampwidth() == 2
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data.astype(np.float64).reshape(-1, 2) / 32767.0


def main():
    np.random.seed(42)
    # --- load voices (trimmed for accurate timing)
    v_intro = trim_silence(decode_voice(os.path.join(RAW, "v_intro.mp3")))
    v_ex = [trim_silence(decode_voice(os.path.join(RAW, f"v_ex{i}.mp3"))) for i in range(1, 6)]
    v_plank = trim_silence(decode_voice(os.path.join(RAW, "v_plank.mp3")))

    # Manual cut points derived from measured silence-gap analysis of each bundle
    cues = split_at(decode_voice(os.path.join(RAW, "v_cues.mp3")), [1.80, 3.85, 4.75])
    half_cue, last10_cue, praise1, praise2 = cues
    rests = split_at(decode_voice(os.path.join(RAW, "v_rest.mp3")), [6.80, 9.54])
    rest_a, rest_b, rest_c = rests
    pcues = split_at(decode_voice(os.path.join(RAW, "v_plank_cues.mp3")), [3.12, 6.68, 10.97, 23.10])
    cheer30, cheer60, cheer90, countdown10, finale = pcues

    print("cue durations (s):")
    for name, s in [("half", half_cue), ("last10", last10_cue), ("praise1", praise1), ("praise2", praise2),
                    ("rest_a", rest_a), ("rest_b", rest_b), ("rest_c", rest_c),
                    ("cheer30", cheer30), ("cheer60", cheer60), ("cheer90", cheer90),
                    ("countdown10", countdown10), ("finale", finale)]:
        print(f"  {name:12s} {len(s)/SR:6.2f}")

    d = lambda x: len(x) / SR
    manifest = {}
    REP = 2.5  # seconds per rep (per the brief)

    # --- intro
    t_v = 0.6
    dur = t_v + d(v_intro) + 2.8
    m = build_track(dur, "calm", [(t_v, v_intro, 1.0)], [(0.05, CHIRP, 0.0)])
    p, sec = write_mp3(m, "01_intro", keep_wav=True)
    manifest["01_intro"] = sec
    print("intro", sec)

    # --- exercises
    ex_meta = [
        ("02_pushups", v_ex[0], 20),
        ("03_squats", v_ex[1], 30),
        ("04_mountain", v_ex[2], 40),
        ("05_jacks", v_ex[3], 50),
        ("06_highknees", v_ex[4], 60),
    ]
    for idx, (name, vs, N) in enumerate(ex_meta):
        t_v = 0.5
        T0 = t_v + d(vs) + 1.3
        voices = [(t_v, vs, 1.0)]
        beeps = [(T0, CHIRP, 0.55)]
        for k in range(1, N):
            sig = ACCENT if (k + 1) % 10 == 0 else BEEP
            beeps.append((T0 + k * REP, sig, 0.5 if sig is BEEP else 0.6))
        end_rep = T0 + N * REP
        if N >= 30 and N // 2 != N - 10:
            voices.append((T0 + (N / 2) * REP - 0.15, half_cue, 1.0))
        voices.append((T0 + (N - 10) * REP - 0.15, last10_cue, 1.0))
        pr = praise1 if idx % 2 == 0 else praise2
        voices.append((end_rep + 0.2, pr, 1.0))
        dur = end_rep + 0.2 + d(pr) + 2.4
        m = build_track(dur, "bright", voices, beeps)
        p, sec = write_mp3(m, name, keep_wav=True)
        manifest[name] = sec
        print(name, f"{sec:.1f}s (reps {N}, beep window {T0:.1f}->{end_rep:.1f})")

    # --- rest 30s template
    tc = 30.2 - d(rest_c)
    voices = [(0.4, rest_a, 1.0), (15.0, rest_b, 1.0), (tc, rest_c, 1.0)]
    dur = max(30.6, tc + d(rest_c)) + 1.4
    beeps = [(t, TICK, 0.22) for t in (5.0, 10.0, 20.0)]
    m = build_track(dur, "calm", voices, beeps, fade_out=1.4)
    p, sec = write_mp3(m, "rest_30s", keep_wav=True)
    manifest["rest_30s"] = sec
    print("rest_30s", sec)

    # --- plank (2 min hold + outro)
    t_v = 0.5
    H0 = t_v + d(v_plank) + 0.35
    voices = [(t_v, v_plank, 1.0),
              (H0 + 30, cheer30, 1.0),
              (H0 + 60, cheer60, 1.0),
              (H0 + 90, cheer90, 1.0),
              (H0 + 120 - d(countdown10), countdown10, 1.0),
              (H0 + 120.5, finale, 1.0)]
    beeps = [(H0 + 15 * k, TICK, 0.25) for k in range(1, 8)]
    beeps.append((H0, CHIRP, 0.5))
    beeps.append((H0 + 120, ACCENT, 0.65))
    dur = H0 + 120.5 + d(finale) + 3.0
    m = build_track(dur, "steady", voices, beeps, fade_out=3.0)
    p, sec = write_mp3(m, "07_plank", keep_wav=True)
    manifest["07_plank"] = sec
    print("plank", sec)

    # --- full workout (ffmpeg concat demuxer, stream copy, 1s gaps)
    order = ["01_intro", "02_pushups", "rest_30s", "03_squats", "rest_30s",
             "04_mountain", "rest_30s", "05_jacks", "rest_30s",
             "06_highknees", "rest_30s", "07_plank"]
    sil = os.path.join(RAW, "silence.mp3")
    subprocess.run([FF, "-y", "-v", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=stereo", "-t", "1", "-b:a", "128k", sil], check=True)
    lst = os.path.join(RAW, "concat.txt")
    lines = []
    for i, nm in enumerate(order):
        lines.append(f"file '{os.path.join(OUT, nm + '.mp3')}'")
        if i < len(order) - 1:
            lines.append(f"file '{sil}'")
    with open(lst, "w") as f:
        f.write("\n".join(lines))
    full_path = os.path.join(OUT, "full_workout.mp3")
    subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", full_path], check=True)
    # duration without loading audio into RAM
    import re
    res = subprocess.run([FF, "-i", full_path], capture_output=True, text=True)
    mm = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    sec = int(mm.group(1)) * 3600 + int(mm.group(2)) * 60 + float(mm.group(3))
    manifest["full_workout"] = sec
    print("full_workout", f"{sec:.1f}s = {sec/60:.1f} min")
    for tmp in (sil, lst):
        os.remove(tmp)
    for nm in order:
        wp = os.path.join(RAW, nm + ".wav")
        if os.path.exists(wp):
            os.remove(wp)
    with open(os.path.join(ROOT, "manifest.json"), "w") as f:
        json.dump({k: round(v, 2) for k, v in manifest.items()}, f, indent=2)
    total = sum(manifest[k] for k in manifest if k != "full_workout")
    print(f"total of parts: {total/60:.1f} min")


if __name__ == "__main__":
    main()
