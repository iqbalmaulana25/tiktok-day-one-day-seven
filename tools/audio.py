#!/usr/bin/env python3
"""Synthesize the soundtrack for the "Day one, day seven" video.

One motif, two energies — the music tells the same story as the picture.
Day one is a slow, sparse, slightly lonely square-wave tune in A minor.
After the patch-note montage the identical motif returns at 140 BPM in
A major with bass, kick, hats, arpeggios and game SFX (seed shots, coin
dings on every kill, a coin shower for the boss). Everything is
synthesized with numpy; no samples, no downloads.

Usage: python3 audio.py <out.wav>   (26.0 s, 44.1 kHz, stereo 16-bit)
"""

import math
import sys

import numpy as np

SR = 44100
DUR = 26.0
N = int(SR * DUR)
mix = np.zeros(N, dtype=np.float64)
rng = np.random.default_rng(20261123)


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(buf_t0, sig):
    i0 = int(buf_t0 * SR)
    i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0:
        mix[i0:i1] += sig[: i1 - i0]


def tone(midi_or_hz, t0, dur, wave="square", gain=0.15, slide_to=None, detune=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi_or_hz if midi_or_hz > 30 else freq(midi_or_hz)
    if slide_to is not None:
        f1 = slide_to if slide_to > 30 else freq(slide_to)
        f = f0 * (f1 / f0) ** (t / dur)
        ph = 2 * np.pi * np.cumsum(f) / SR
    else:
        f = f0 * 2 ** (detune / 1200)
        ph = 2 * np.pi * f * t
    if wave == "square":
        sig = np.sign(np.sin(ph)) * 0.6 + 0.4 * np.sin(ph)
    elif wave == "saw":
        sig = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif wave == "tri":
        sig = 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    else:
        sig = np.sin(ph)
    env = np.minimum(1, t / 0.012) * np.exp(-2.2 * t / dur)
    add(t0, sig * env * gain)


def kick(t0, gain=0.5):
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    f = 120 * (45 / 120) ** (t / 0.14)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-26 * t)
    add(t0, sig * gain)


def noise(t0, dur, gain, kind="hat"):
    n = int(dur * SR)
    w = rng.standard_normal(n)
    if kind == "hat":
        sig = np.diff(np.concatenate([[0], w])) * np.exp(-90 * np.arange(n) / SR)
    elif kind == "snare":
        sig = w * np.exp(-30 * np.arange(n) / SR)
        sig = sig - np.convolve(sig, np.ones(24) / 24, mode="same")
    else:  # whoosh: slow swell
        tt = np.arange(n) / SR
        sig = w * np.sin(np.pi * tt / dur) ** 2
        sig = np.convolve(sig, np.ones(90) / 90, mode="same")
    add(t0, sig * gain)


def ding(t0, hz, gain=0.12, dur=0.16):
    tone(hz, t0, dur, wave="sine", gain=gain)
    tone(hz * 2, t0, dur * 0.6, wave="sine", gain=gain * 0.35)


# ---------------------------------------------------------------- day one
# A slow, sleepy tune: one voice, long gaps. A3 C4 E4 A4 E4 C4 B3 A3.
day1_notes = [57, 60, 64, 69, 64, 60, 59, 57]
for i, m in enumerate(day1_notes):
    t0 = 0.12 + i * 0.635
    if t0 > 5.0:
        break
    tone(m, t0, 0.55, wave="square", gain=0.085)
    tone(m, t0, 0.55, wave="square", gain=0.04, detune=-7)
# the sprout's hopeful little shots (and the dirt puffs where they land)
for t0 in (1.3, 2.6, 3.9):
    tone(72, t0, 0.09, wave="sine", gain=0.05, slide_to=64)
    noise(t0 + 0.47, 0.07, 0.05, kind="snare")
# a tired yawn as the segment ends
tone(310, 4.55, 0.55, wave="saw", gain=0.035, slide_to=88)
# soft thud under the DAY 1 slam
kick(0.05, gain=0.30)

# ---------------------------------------------------------------- montage
for k in range(6):  # calendar flips
    noise(5.2 + k * 0.5, 0.16, 0.10, kind="whoosh")
for i, t0 in enumerate((5.75, 6.25, 6.75, 7.25, 7.75)):  # patch-note pops
    ding(t0, 540 + i * 110, gain=0.11, dur=0.12)
for i, m in enumerate((72, 76, 79, 84)):  # rising arp into the reveal
    tone(m, 7.78 + i * 0.1, 0.16, wave="square", gain=0.09)

# ---------------------------------------------------------------- day seven groove
BPM = 140
BEAT = 60 / BPM
GROOVE_T0, GROOVE_T1 = 8.2, 23.5
# chord roots per bar: A, E, F#m, D (MIDI), with chord tones for the arp
BARS = [
    (45, [69, 73, 76]),
    (40, [68, 71, 76]),
    (42, [69, 73, 78]),
    (38, [66, 69, 74]),
]
LEAD = [  # one bar of 16 steps (None = rest), scale degrees into a bright riff
    [0, None, 2, None, 3, None, 2, 1, 0, None, 2, None, 4, 3, 2, None],
    [0, None, 2, None, 3, None, 4, None, 3, 2, 1, None, 2, None, None, None],
    [4, None, 3, 2, 3, None, 2, None, 1, 2, 3, None, 2, 1, 0, None],
    [0, None, 2, None, 3, None, 2, 1, 0, None, 1, 2, None, None, None, None],
]
PENTA = [0, 2, 4, 7, 9, 12, 14, 16]

bar = 0
t = GROOVE_T0
while t < GROOVE_T1:
    root, chord = BARS[bar % 4]
    # bass: eighth notes, root with an octave bounce
    for s in range(8):
        tt = t + s * BEAT / 2
        if tt >= GROOVE_T1:
            break
        tone(root + (12 if s % 4 == 2 else 0), tt, 0.16, wave="tri", gain=0.20)
    # drums
    for b in range(4):
        tt = t + b * BEAT
        if tt < GROOVE_T1:
            kick(tt, gain=0.42)
        if b in (1, 3) and tt < GROOVE_T1:
            noise(tt, 0.09, 0.13, kind="snare")
        for s in range(2):
            ht = tt + s * BEAT / 2 + BEAT / 4
            if ht < GROOVE_T1:
                noise(ht, 0.03, 0.05, kind="hat")
    # arp: 16ths cycling the chord tones, two octaves up
    for s in range(16):
        tt = t + s * BEAT / 4
        if tt >= GROOVE_T1:
            break
        tone(chord[s % 3] + 12, tt, 0.09, wave="tri", gain=0.045)
    # lead riff
    for s, deg in enumerate(LEAD[bar % 4]):
        if deg is None:
            continue
        tt = t + s * BEAT / 4
        if tt >= GROOVE_T1:
            break
        tone(chord[0] + PENTA[deg % len(PENTA)], tt, 0.14, wave="square", gain=0.075)
    t += BEAT * 4
    bar += 1

# seed-shot pews sprinkled through the fight, and coin dings on the kills
for k in range(26):
    tt = 9.3 + k * 0.43
    if tt < 19.6:
        tone(950 + (k % 5) * 60, tt, 0.055, wave="square", gain=0.028, slide_to=320)
ding(13.3, 1568, gain=0.11)
ding(13.38, 2093, gain=0.09)
ding(15.7, 1568, gain=0.11)
ding(15.78, 2093, gain=0.09)
# the DAY 7 slam lands with the groove
kick(8.2, gain=0.55)
noise(8.2, 0.12, 0.16, kind="snare")

# ---------------------------------------------------------------- finale
# boss coin shower at 21.5, then a victory jingle over the groove
for i, hz in enumerate((1318, 1568, 1760, 2093, 2349, 2637, 3136)):
    ding(21.5 + i * 0.07, hz, gain=0.10, dur=0.14)
for i, m in enumerate((72, 76, 79, 84, 88)):
    tone(m, 21.95 + i * 0.11, 0.34, wave="square", gain=0.085)
tone(69, 22.5, 0.9, wave="tri", gain=0.07)
tone(73, 22.5, 0.9, wave="tri", gain=0.07)
tone(76, 22.5, 0.9, wave="tri", gain=0.07)

# ---------------------------------------------------------------- master
# gentle fade in, and the music bows out under the end card
tt = np.arange(N) / SR
master = np.minimum(1, tt / 0.05)
fade = np.clip((25.95 - tt) / 1.3, 0, 1)
mix *= master * np.where(tt > 24.6, fade, 1.0)
mix = np.tanh(mix * 1.15)
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
stereo = np.stack([mix, mix * 0.99], axis=1)
pcm = (stereo * 32767).astype("<i2")
import wave as wav

with wav.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", sys.argv[1], DUR, "s, peak", round(float(peak), 3))
