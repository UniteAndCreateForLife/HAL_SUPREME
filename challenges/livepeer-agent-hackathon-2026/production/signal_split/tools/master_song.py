"""Master a song for release loudness: corrective EQ, width above the bass, glue compression, light saturation, limiting.

Usage: python tools/master_song.py <song.wav> <out.wav> [target_lufs]

The chain answers what the analysis of the raw MiniMax take showed: heavy 250-500 Hz, a dip at 2-4 kHz (vocal presence),
little air above 8 kHz, a narrow image (side 11 dB under mid) and a 17 dB crest factor.
  - high-pass at 28 Hz; -2 dB at 300 Hz; +2 dB at 3.2 kHz; +2.5 dB shelf from 10 kHz
  - a 4th-order crossover at 150 Hz: bass summed to mono, everything above widened by 25%
  - a 2.5:1 glue compressor, then a tanh soft clipper that shaves a few dB off the transient peaks, so the limiter
    works about 4 dB instead of 17 (measured on this take)
  - a limiter at a -3 dBFS ceiling, run 4x oversampled: AAC adds about 2.5 dB of overshoot to a limited master
The gain into the limiter is searched so the integrated loudness lands on the target (default -10 LUFS)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FF = ["ffmpeg", "-hide_banner", "-y"]
CHAIN = ("highpass=f=28,equalizer=f=300:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.2:g=2,treble=g=2.5:f=10000,"
         "asplit=2[a][b];[a]acrossover=split=150:order=4th[lo][hi];[lo]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1[lom];"
         "[hi]extrastereo=m=1.25[hiw];[lom][hiw]amix=inputs=2:normalize=0[wide];[b]anullsink;"
         "[wide]acompressor=threshold=-20dB:ratio=2.5:attack=20:release=180:makeup=3,volume=2dB,asoftclip=type=tanh:threshold=0.85,"
         "volume=-1dB")


def measure(path: Path) -> dict:
    text = subprocess.run([*FF, "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    return {"integrated_lufs": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", text)[-1]),
            "lra_lu": float(re.findall(r"LRA:\s+(-?[\d.]+) LU", text)[-1]),
            "true_peak_dbtp": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)[-1])}


def render(song: Path, out: Path, gain_db: float) -> dict:
    graph = (f"[0:a]{CHAIN},volume={gain_db:.2f}dB,aresample=192000,"  # 4x oversampling so the limiter also catches inter-sample peaks
             f"alimiter=limit=0.708:attack=4:release=80:level=false,aresample=48000[out]")
    subprocess.run([*FF, "-loglevel", "error", "-i", str(song), "-filter_complex", graph, "-map", "[out]", "-ar", "48000",
                    "-c:a", "pcm_s24le", str(out)], check=True)
    return measure(out)


def master(song: Path, out: Path, target: float = -10.0) -> dict:
    low, high, best = -4.0, 8.0, None
    for _ in range(7):  # bisection on the drive into the limiter
        gain = (low + high) / 2
        result = render(song, out, gain)
        best = {"gain_db": round(gain, 2), **result}
        if abs(result["integrated_lufs"] - target) < 0.25:
            break
        if result["integrated_lufs"] < target:
            low = gain
        else:
            high = gain
    return {"input": measure(song), "output": best, "target_lufs": target, "chain": CHAIN}


if __name__ == "__main__":
    report = master(Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else -10.0)
    Path(sys.argv[2]).with_suffix(".master.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("input", "output", "target_lufs")}, indent=1))
