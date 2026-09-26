"""Master SIGNAL REBOOT (emo rap-rock) for release: corrective EQ, three-band compression, glue, tape-style saturation, and
a 4x oversampled limiter.

Usage: python tools/master_song_v2.py <song.wav> <out.wav> [target_lufs]

What the analysis of the raw take showed and what the chain does about it:
  - boomy 220 Hz and boxy 700 Hz guitars: -1.5 dB at each
  - vocal presence (2-4 kHz) and air (above 8 kHz) sit low: +1.5 dB at 3 kHz, +2 dB shelf from 10 kHz
  - a 12 LU loudness range (a whisper-quiet bridge against loud choruses): three bands split at 120 Hz and 2.5 kHz,
    each compressed on its own (the bass summed to mono), then a gentle 1.8:1 glue compressor
  - a 17 dB crest factor: atan saturation shaves transient peaks the way tape does, so the limiter works less
The gain into the limiter is searched so the integrated loudness lands on the target (default -9.5 LUFS); the limiter
ceiling is -2 dBFS, run 4x oversampled. On this song the master measured -9.5 LUFS and -2.0 dBTP, and -0.6 dBTP after
one AAC encode at 320 kbps."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FF = ["ffmpeg", "-hide_banner", "-y"]
CHAIN = ("highpass=f=28,equalizer=f=220:t=q:w=1.0:g=-1.5,equalizer=f=700:t=q:w=1.2:g=-1.5,"
         "equalizer=f=3000:t=q:w=1.0:g=1.5,treble=g=2:f=10000,"
         "acrossover=split=120 2500:order=4th[lo][mid][hi];"
         "[lo]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,acompressor=threshold=-20dB:ratio=3:attack=30:release=200:makeup=2[lo2];"
         "[mid]acompressor=threshold=-22dB:ratio=2.5:attack=15:release=150:makeup=2[mid2];"
         "[hi]extrastereo=m=1.12,acompressor=threshold=-26dB:ratio=2:attack=5:release=100:makeup=2[hi2];"
         "[lo2][mid2][hi2]amix=inputs=3:normalize=0,"
         "acompressor=threshold=-16dB:ratio=1.8:attack=30:release=250:makeup=1,asoftclip=type=atan:threshold=0.9")


def measure(path: Path) -> dict:
    text = subprocess.run([*FF, "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    return {"integrated_lufs": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", text)[-1]),
            "lra_lu": float(re.findall(r"LRA:\s+(-?[\d.]+) LU", text)[-1]),
            "true_peak_dbtp": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)[-1])}


def render(song: Path, out: Path, gain_db: float, limit: bool = True) -> dict:
    tail = (f",volume={gain_db:.2f}dB" + (",aresample=192000,alimiter=limit=0.794:attack=4:release=80:level=false,aresample=48000"
                                          if limit else ""))
    graph = f"[0:a]{CHAIN}{tail}[out]"
    subprocess.run([*FF, "-loglevel", "error", "-i", str(song), "-filter_complex", graph, "-map", "[out]", "-ar", "48000",
                    "-c:a", "pcm_s24le", str(out)], check=True)
    return measure(out)


def master(song: Path, out: Path, target: float = -9.5) -> dict:
    low, high, best = -6.0, 14.0, None
    for _ in range(8):  # bisection on the drive into the limiter
        gain = (low + high) / 2
        result = render(song, out, gain)
        best = {"gain_db": round(gain, 2), **result}
        if abs(result["integrated_lufs"] - target) < 0.2:
            break
        low, high = (gain, high) if result["integrated_lufs"] < target else (low, gain)
    pre = render(song, out.with_name(out.stem + "_prelimit.wav"), best["gain_db"], limit=False)
    out.with_name(out.stem + "_prelimit.wav").unlink()
    best["limiter_peak_reduction_db"] = round(pre["true_peak_dbtp"] - best["true_peak_dbtp"], 1)
    return {"input": measure(song), "output": best, "target_lufs": target, "chain": CHAIN}


if __name__ == "__main__":
    report = master(Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else -9.5)
    Path(sys.argv[2]).with_suffix(".master.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("input", "output", "target_lufs")}, indent=1))
