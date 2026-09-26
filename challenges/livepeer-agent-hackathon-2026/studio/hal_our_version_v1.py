#!/usr/bin/env python3
"""HAL Our Version v1: learn the owner's sound by remaking the owner's own songs and scoring every remake.

For each song the owner posted, HAL writes a brief in original words, the takes are generated upstream
(MiniMax Music 3 through Livepeer credits), hal_song_pipeline_v1 puts the owner's authorized voice on them and
masters them, and this module scores each take against the original. Scores and the owner's keep/reject
verdicts train a small learner (Thompson sampling over brief choices), so each round of briefs moves closer
to the owner's sound.

Stages:
  catalog  yt-dlp metadata (JSON lines, read-only) -> uploads classified and ranked by engagement
  analyze  audio -> tempo, key, loudness, energy curve, style fingerprint and style tags (MuQ-MuLan)
  brief    analysis + learner -> a generation prompt in original words; artist names are refused
  score    original vs take -> style match, catalog rank, lyric error, loudness -> reward in [0, 1]
  verdict  the owner's keep or reject, which counts three times as much as an automatic score

Evidence: events go to HAL's EventStore; learning events share the subject "our_version.learner", so the
learner is rebuilt from canonical history on every run. Files under data/our_version/ are rebuildable
projections. No stage generates, spends, publishes or writes to live playback.

Usage:
  python scripts/hal_our_version_v1.py catalog --ytdlp <uploads.jsonl> [--out data/our_version/catalog_v1.json]
  python scripts/hal_our_version_v1.py analyze --audio <song.wav> --id <song_id> [--lyrics]
  python scripts/hal_our_version_v1.py brief --id <song_id> [--seconds 180] [--seed N]
  python scripts/hal_our_version_v1.py score --id <song_id> --take <take.wav> --brief <brief.json> [--receipt <pipeline receipt>]
  python scripts/hal_our_version_v1.py verdict --score <score.json> (--keep | --reject)
"""

from __future__ import annotations

import argparse
import os
import hashlib
import json
import math
import random
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(os.environ.get("HAL_ROOT", Path(__file__).resolve().parents[1]))  # the private tree sets HAL_ROOT
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

STATE = ROOT / "data" / "our_version"
MULAN_CACHE = ROOT / "temp" / "opencode" / "DiffRhythm" / "pretrained"
SOURCE = "hal_our_version_v1"
LEARNER_SUBJECT = "our_version.learner"
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler key profiles.
_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# Generic style words MuLan scores each song against. Genre, vocal and mood terms only: never artist names.
STYLE_VOCAB = [
    "dark electronic", "industrial", "glitch pop", "hyperpop", "trap", "plugg rap", "melodic rap", "emo rap",
    "experimental trap", "surreal comedic rap", "dubstep", "bass music", "synthwave", "darkwave", "dream pop",
    "cinematic", "ambient", "techno", "trance", "drum and bass", "punk", "post-punk", "alternative rock",
    "nu metal", "gothic", "experimental", "pop", "r&b", "lo-fi", "psychedelic",
    "male vocals", "female vocals", "screamed vocals", "whispered vocals", "autotuned vocals", "rapped vocals",
    "spoken word", "choir", "instrumental", "distorted guitar", "808 bass", "heavy drums", "piano", "strings",
    "synth arpeggio", "vocal chops", "aggressive", "melancholic", "euphoric", "eerie", "playful", "hypnotic",
    "anthemic", "chaotic", "tender",
]

# What the learner chooses for each brief, on top of the original's own style tags.
CHOICES: dict[str, list[str]] = {
    "vocal": ["whispered close-mic lead", "autotuned melodic lead", "half-sung, half-rapped lead",
              "stacked falsetto hook", "pitched vocal chops answering the lead"],
    "texture": ["bitcrushed glitch edits", "detuned synth pads", "bright ringtone plucks",
                "tape-warped samples", "wide supersaw lifts"],
    "drums": ["hard 808s with rolling hi-hats", "half-time dubstep drums", "four-on-the-floor kick",
              "broken glitch percussion"],
    "arc": ["slow build to a heavy drop", "hook first, then verses", "quiet verses, explosive chorus",
            "steady hypnotic groove"],
    # The first pilot take came back vocal-dominated; the owner's songs are production-led. Structure is learned too.
    "structure": ["vocal-forward song", "instrumental drops between sections", "instrumental intro and outro"],
}


def arrange_lyrics(lyrics: str, structure: str | None) -> str:
    """Section tags that give a sung-song model room for the production: drops between blocks, or bookends."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", str(lyrics or "")) if block.strip()]
    if not blocks or structure in (None, "vocal-forward song"):
        return "\n\n".join(blocks)
    if structure == "instrumental drops between sections":
        out = []
        for index, block in enumerate(blocks, 1):
            out.append(block)
            if index % 2 == 0 and index < len(blocks):
                out.append("[instrumental]")
        return "\n\n".join(out)
    if structure == "instrumental intro and outro":
        return "\n\n".join(["[intro]"] + blocks + ["[outro]"])
    return "\n\n".join(blocks)

_REVIEW = re.compile(r"SHAPE OF SIGNAL|VOICE IN THE GLASS|\bREVIEW\b|IDENTITY REWORK|WATCH NOW|PREVIEW|CANARY|"
                     r"\bPROOF\b|\bTEST\b", re.I)
_NON_SONG = re.compile(r"INTERVIEW|\bAD\b|ADVERTISE|TIK ?TOK|PLAYFUL (COMPUTER|CARTOON)|\bEPISODE\b|\bEP ?\d+", re.I)
_COVER = re.compile(r"\bcover\b", re.I)
# "Artist - Title (… Remix)" by someone other than the owner is a third-party remix.
_CREDITED_REMIX = re.compile(r"^\s*([^-–—|(]+?)\s+[-–—]\s+.+\([^)]*\bremix\b[^)]*\)", re.I)
OWN_NAMES = {"hal", "hal supreme", "jakob", "unite and create for life"}
MIN_SONG_SECONDS = 45


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- catalog

def classify_upload(row: dict[str, Any]) -> str:
    """own_song, third_party (covers and remixes of other artists), non_song (episodes, ads, shorts) or hal_review."""
    title = str(row.get("title") or "")
    if _REVIEW.search(title):
        return "hal_review"
    credited = _CREDITED_REMIX.match(title)
    if _COVER.search(title) or (credited and credited.group(1).strip().lower() not in OWN_NAMES):
        return "third_party"
    if _NON_SONG.search(title) or float(row.get("duration") or 0) < MIN_SONG_SECONDS:
        return "non_song"
    return "own_song"


def engagement(row: dict[str, Any]) -> int:
    """Views, plus 10 per like and 20 per comment: a comment or a like is a far stronger signal than a view."""
    return int(row.get("view_count") or 0) + 10 * int(row.get("like_count") or 0) + 20 * int(row.get("comment_count") or 0)


def build_catalog(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    uploads = []
    for row in rows:
        uploads.append({"id": row.get("id"), "title": row.get("title"), "duration_s": row.get("duration"),
                        "upload_date": row.get("upload_date"), "views": row.get("view_count"),
                        "likes": row.get("like_count"), "comments": row.get("comment_count"),
                        "class": classify_upload(row), "engagement": engagement(row)})
    uploads.sort(key=lambda item: -item["engagement"])
    counts: dict[str, int] = {}
    for item in uploads:
        counts[item["class"]] = counts.get(item["class"], 0) + 1
    return {"schema": "hal.our_version.catalog.v1", "created_at_utc": utc_now(), "authority": "DERIVED_REBUILDABLE",
            "counts": counts, "uploads": uploads}


# ---------------------------------------------------------------- analysis

def estimate_key(chroma_mean: np.ndarray) -> dict[str, Any]:
    """Best Krumhansl-Kessler match; confidence is the margin over the runner-up correlation."""
    chroma = np.asarray(chroma_mean, dtype=float)
    scores = []
    for tonic in range(12):
        for mode, profile in (("major", _MAJOR), ("minor", _MINOR)):
            scores.append((float(np.corrcoef(chroma, np.roll(profile, tonic))[0, 1]), f"{NOTES[tonic]} {mode}"))
    scores.sort(reverse=True)
    return {"key": scores[0][1], "correlation": round(scores[0][0], 3),
            "confidence": round(scores[0][0] - scores[1][0], 3)}


def energy_curve(y: np.ndarray, sr: int, window_s: float = 5.0) -> list[float]:
    """RMS level in dBFS per window: the song's loud and quiet shape."""
    hop = max(1, int(window_s * sr))
    levels = []
    for start in range(0, len(y), hop):
        chunk = y[start:start + hop]
        rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
        levels.append(round(20 * math.log10(max(rms, 1e-9)), 1))
    return levels


def integrated_lufs(y: np.ndarray, sr: int) -> float | None:
    try:
        import pyloudnorm  # noqa: PLC0415

        value = float(pyloudnorm.Meter(sr).integrated_loudness(y))
        return round(value, 2) if math.isfinite(value) else None
    except Exception:  # noqa: BLE001 - loudness is evidence, never a crash
        return None


class MuLanEmbedder:
    """MuQ-MuLan style fingerprints from the locally cached weights; nothing is downloaded."""

    def __init__(self, cache_dir: Path = MULAN_CACHE, device: str | None = None, window_s: float = 10.0,
                 max_windows: int = 12):
        self.cache_dir, self.device, self.window_s, self.max_windows = cache_dir, device, window_s, max_windows
        self._model = None

    def _load(self):
        if self._model is None:
            import os  # noqa: PLC0415

            os.environ["HF_HUB_OFFLINE"] = "1"
            import torch  # noqa: PLC0415
            from muq import MuQMuLan  # noqa: PLC0415

            self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._model = MuQMuLan.from_pretrained("OpenMuQ/MuQ-MuLan-large", cache_dir=str(self.cache_dir))
            self._model = self._model.to(self.device).eval()
        return self._model

    def embed_audio(self, path: Path) -> np.ndarray:
        import librosa  # noqa: PLC0415
        import torch  # noqa: PLC0415

        model = self._load()
        wav, _ = librosa.load(str(path), sr=24000, mono=True)
        hop = int(self.window_s * 24000)
        starts = list(range(0, max(1, len(wav) - hop), hop))
        if len(starts) > self.max_windows:  # spread the windows across the whole song
            starts = [starts[int(i * (len(starts) - 1) / (self.max_windows - 1))] for i in range(self.max_windows)]
        chunks = np.stack([np.pad(wav[s:s + hop], (0, max(0, hop - len(wav[s:s + hop])))) for s in starts])
        with torch.no_grad():
            emb = model(wavs=torch.tensor(chunks, dtype=torch.float32, device=self.device)).float()
        return unit(emb.mean(0).cpu().numpy())

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        import torch  # noqa: PLC0415

        with torch.no_grad():
            emb = self._load()(texts=texts).float().cpu().numpy()
        return np.stack([unit(row) for row in emb])


def unit(vector: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(vector) if not isinstance(vector, np.ndarray) else vector, dtype=float)
    norm = float(np.linalg.norm(array))
    return array / norm if norm else array


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    return round(float(np.dot(unit(a), unit(b))), 4)


def style_tags(vector: np.ndarray, vocab_vectors: np.ndarray, vocab: list[str] = STYLE_VOCAB, top: int = 8) -> list[list]:
    scores = vocab_vectors @ unit(vector)
    order = np.argsort(-scores)[:top]
    return [[vocab[i], round(float(scores[i]), 3)] for i in order]


def lyric_lines_from_words(words: list[Any], gap_s: float = 0.6, max_words: int = 10) -> list[str]:
    """Group timed words into sung lines at pauses, so a transcript reads as lyrics."""
    lines, current, last_end = [], [], None
    for word in words:
        if isinstance(word, (tuple, list)):  # hal_lyric_timeline_v1.TimedWord: (token, start, end)
            text, start, end = str(word[0]).strip(), float(word[1]), float(word[2])
        else:
            text = str(word.get("word") or "").strip()
            start = float(word.get("start") or 0.0)
            end = float(word.get("end") or start)
        if current and ((last_end is not None and start - last_end > gap_s) or len(current) >= max_words):
            lines.append(" ".join(current))
            current = []
        if text:
            current.append(text)
        last_end = end
    if current:
        lines.append(" ".join(current))
    return lines


def tag_sections(lines: list[str], block: int = 4, similarity: float = 0.75) -> str:
    """[Verse]/[Chorus] tags a song generator understands: a block whose lines mostly recur elsewhere is a chorus.

    Recurrence is fuzzy, because a transcriber hears the same sung line a little differently each time."""
    from difflib import SequenceMatcher  # noqa: PLC0415

    normalized = [re.sub(r"[^a-z0-9 ]", "", line.lower()).strip() for line in lines]

    def recurs(index: int) -> bool:
        return any(other != index and normalized[index] and
                   SequenceMatcher(None, normalized[index], normalized[other]).ratio() >= similarity
                   for other in range(len(lines)))

    recurring = [recurs(index) for index in range(len(lines))]
    out = []
    for start in range(0, len(lines), block):
        chunk = lines[start:start + block]
        repeated = sum(1 for index in range(start, start + len(chunk)) if recurring[index])
        out.append("[Chorus]" if repeated * 2 > len(chunk) else "[Verse]")
        out.extend(chunk)
        out.append("")
    return "\n".join(out).strip()


def analyze_audio(path: Path, embedder: Any = None, vocab_vectors: np.ndarray | None = None,
                  sr: int = 22050) -> dict[str, Any]:
    import librosa  # noqa: PLC0415

    y, sr = librosa.load(str(path), sr=sr, mono=True)
    # The tempo estimate itself: beat_track reports 0 when its beat tracker finds too few onsets.
    tempo = librosa.feature.tempo(onset_envelope=librosa.onset.onset_strength(y=y, sr=sr), sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    result: dict[str, Any] = {
        "file": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "duration_s": round(len(y) / sr, 2), "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 1),
        "key": estimate_key(chroma), "lufs_mono": integrated_lufs(y, sr), "energy_db_5s": energy_curve(y, sr),
    }
    if embedder is not None:
        vector = embedder.embed_audio(Path(path))
        result["style_vector"] = [round(float(v), 6) for v in vector]
        if vocab_vectors is not None:
            result["style_tags"] = style_tags(vector, vocab_vectors)
    return result


# ---------------------------------------------------------------- learning

@dataclass
class Learner:
    """Thompson sampling over brief choices, one Beta posterior per (style context, dimension, option)."""

    stats: dict[str, list[float]] = field(default_factory=dict)

    @staticmethod
    def key(context: str, dimension: str, option: str) -> str:
        return f"{context}|{dimension}|{option}"

    def sample(self, context: str, rng: random.Random, choices: dict[str, list[str]] = CHOICES) -> dict[str, str]:
        picked = {}
        for dimension, options in choices.items():
            draws = []
            for option in options:
                alpha, beta = self.stats.get(self.key(context, dimension, option), [1.0, 1.0])
                draws.append((rng.betavariate(alpha, beta), option))
            picked[dimension] = max(draws)[1]
        return picked

    def update(self, context: str, picked: dict[str, str], reward: float, weight: float = 1.0) -> None:
        reward = min(1.0, max(0.0, float(reward)))
        for dimension, option in picked.items():
            alpha, beta = self.stats.get(self.key(context, dimension, option), [1.0, 1.0])
            self.stats[self.key(context, dimension, option)] = [alpha + weight * reward, beta + weight * (1 - reward)]

    @classmethod
    def from_events(cls, events: Iterable[Any]) -> "Learner":
        """Replay canonical history: the latest automatic score per take (a rescore corrects, never double counts),
        plus every owner verdict."""
        learner = cls()
        latest: dict[str, dict[str, Any]] = {}
        verdicts: list[dict[str, Any]] = []
        for index, event in enumerate(events):
            payload = event.payload if hasattr(event, "payload") else event.get("payload", {})
            if payload.get("kind") == "reward":
                latest[str(payload.get("take_sha256") or f"event-{index}")] = payload
            elif payload.get("kind") == "verdict":
                verdicts.append(payload)
        for payload in list(latest.values()) + verdicts:
            learner.update(payload["context"], payload["choices"], payload["reward"], payload.get("weight", 1.0))
        return learner


def context_of(analysis: dict[str, Any]) -> str:
    """The learner keeps separate statistics per style family, keyed by the original's strongest genre tag."""
    genre_words = set(STYLE_VOCAB[:30])
    for tag, _score in analysis.get("style_tags") or []:
        if tag in genre_words:
            return tag
    return "unknown"


# ---------------------------------------------------------------- brief

def refuse_names(text: str, banned: Iterable[str]) -> None:
    lowered = text.lower()
    for name in banned:
        name = str(name).strip().lower()
        if name and re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", lowered):
            raise ValueError(f"brief names a real artist ({name!r}); describe the sound in original words instead")


def build_brief(song_id: str, analysis: dict[str, Any], picked: dict[str, str], banned: Iterable[str],
                seconds: int = 180, lyrics: str | None = None) -> dict[str, Any]:
    genre_words = set(STYLE_VOCAB[:30])
    tags = [tag for tag, _ in (analysis.get("style_tags") or []) if tag in genre_words][:3]
    vocal_tags = [tag for tag, _ in (analysis.get("style_tags") or []) if tag.endswith("vocals")][:1]
    structure = picked.get("structure")
    # Production words first: generators weight the start of a prompt, and the owner's songs are production-led.
    parts = tags + [picked[d] for d in ("texture", "drums", "arc") if d in picked]
    if structure == "instrumental drops between sections":
        parts.append("production-led, long instrumental drops between vocal sections")
    parts += vocal_tags + ([picked["vocal"]] if "vocal" in picked else [])
    parts += [f"{round(float(analysis.get('tempo_bpm') or 0))} BPM", (analysis.get("key") or {}).get("key", "")]
    prompt = ", ".join(part for part in parts if part)
    refuse_names(prompt, banned)  # the prompt steers the sound; the owner's lyrics may name people and stay the owner's words
    return {"schema": "hal.our_version.brief.v1", "song_id": song_id, "created_at_utc": utc_now(),
            "context": context_of(analysis), "choices": picked, "prompt": prompt,
            "lyrics": arrange_lyrics(lyrics or "", structure),
            "seconds": int(min(seconds, max(30, analysis.get("duration_s") or seconds)))}


RESTORE_SYSTEM = ("You restore song lyrics from an automatic transcript of the artist's own recording. The words are "
                  "the artist's; you only repair what the transcriber misheard. Output JSON only.")


def lyric_word_similarity(a: str, b: str) -> float:
    """Word-sequence similarity (0..1) ignoring section tags, case and punctuation."""
    from difflib import SequenceMatcher  # noqa: PLC0415

    def words(text: str) -> list[str]:
        return re.findall(r"[a-z0-9']+", re.sub(r"\[[^\]]*\]", " ", str(text).lower()))

    return SequenceMatcher(None, words(a), words(b), autojunk=False).ratio()


def first_json_object(text: str) -> dict[str, Any] | None:
    """The first JSON object in a model reply; code fences, thinking blocks and chatter are tolerated."""
    text = re.sub(r"<think>.*?</think>", "", str(text or ""), flags=re.S)
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, flags=re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def restore_lyrics(raw: str, complete: Any, min_similarity: float = 0.8) -> dict[str, Any]:
    """Repair clear mishearings and mark sections, but keep the artist's words: a restoration that changes more than
    about a fifth of them is rejected in code and the raw transcript is used instead."""
    user = ("TRANSCRIPT (tags are rough blocks, not real sections):\n" + raw + "\n\n"
            "Return JSON {\"lyrics\": \"...\", \"changed\": [{\"from\": \"...\", \"to\": \"...\"}]}.\n"
            "Rules: keep every word that already makes sense. Fix only words that are clearly misheard, choosing the most "
            "likely sung words. Keep the order of lines. Do not add lines, ideas or rhymes. Put section tags on their own "
            "lines: [verse], [chorus] for lines that return, [bridge], [outro].")
    try:
        data = first_json_object(complete(RESTORE_SYSTEM, user)) or {}
    except Exception as exc:  # noqa: BLE001 - restoration is optional; the raw words still work
        return {"lyrics": raw, "restored": False, "reason": f"{type(exc).__name__}: {exc}"[:200]}
    restored = str(data.get("lyrics") or "").strip()
    similarity = lyric_word_similarity(raw, restored) if restored else 0.0
    if similarity < min_similarity:
        return {"lyrics": raw, "restored": False, "similarity": round(similarity, 3),
                "reason": "restoration changed too many of the artist's words"}
    return {"lyrics": restored, "restored": True, "similarity": round(similarity, 3),
            "changed": [c for c in data.get("changed") or [] if isinstance(c, dict)][:60]}


# ---------------------------------------------------------------- scoring

def catalog_rank(take_vector: Iterable[float], original_id: str, catalog: dict[str, Iterable[float]]) -> int | None:
    """1 when the take is closer to its own original than to any other song in the catalog."""
    if original_id not in catalog or len(catalog) < 2:
        return None
    ranked = sorted(catalog, key=lambda song: -cosine(take_vector, catalog[song]))
    return ranked.index(original_id) + 1


def reward(style: float, rank: int | None = None, take_wer: float | None = None,
           original_wer: float | None = None, lufs: float | None = None, in_time: bool | None = None) -> dict[str, Any]:
    """Reward in [0, 1] and a pass flag. Style alone cannot hear timing: a remix whose beat drifts off the vocal
    (hal_remix_v1 fit QC) loses the timing share and can never pass."""
    parts: dict[str, tuple[float, float]] = {"style": (min(1.0, max(0.0, (style - 0.50) / 0.40)), 0.5)}
    if in_time is not None:
        parts["timing"] = (1.0 if in_time else 0.0, 0.4)
    if rank is not None:
        parts["rank"] = (1.0 if rank == 1 else 0.5 if rank <= 3 else 0.0, 0.2)
    if take_wer is not None:
        slack = max(0.0, take_wer - (original_wer if original_wer is not None else 0.0))
        parts["words"] = (min(1.0, max(0.0, 1.0 - slack / 0.30)), 0.2)
    if lufs is not None:
        parts["loudness"] = (1.0 if abs(lufs + 14) <= 1.0 else 0.5 if abs(lufs + 14) <= 3.0 else 0.0, 0.1)
    total = sum(value * weight for value, weight in parts.values()) / sum(weight for _, weight in parts.values())
    if in_time is False:  # off the beat is unusable, however close the style: cap it, do not average it away
        total = min(total, 0.2)
    passed = (style >= 0.75 and (rank is None or rank == 1)
              and (take_wer is None or take_wer <= (original_wer or 0.0) + 0.05)
              and (lufs is None or abs(lufs + 14) <= 1.0)
              and in_time is not False)
    return {"reward": round(total, 4), "components": {k: round(v, 4) for k, (v, _) in parts.items()}, "pass": passed}


# ---------------------------------------------------------------- evidence

def event_store(path: Path | None = None):
    from hal_cognition.event_store import EventStore, get_event_store  # noqa: PLC0415

    return EventStore(db_path=path) if path else get_event_store()


def record(store: Any, event_type: str, subject: str, payload: dict[str, Any]) -> Any:
    from hal_cognition.event_store import Authority, Event  # noqa: PLC0415

    return store.append(Event(source=SOURCE, event_type=event_type, subject=subject, payload=payload,
                              authority=Authority.DERIVED.value, trace_id=f"our_version:{payload.get('song_id', '')}"))


def learner_from_store(store: Any) -> Learner:
    return Learner.from_events(store.get_by_subject(LEARNER_SUBJECT, limit=10000))


def banned_names(catalog_path: Path = STATE / "banned_names.json") -> list[str]:
    """Artist names the owner tagged on uploads, plus the composer's public-figure list: never in a brief."""
    names = set()
    if catalog_path.exists():
        names.update(json.loads(catalog_path.read_text(encoding="utf-8")))
    try:
        from hal_song_composer import _PUBLIC_FIGURE_REFERENCES  # noqa: PLC0415

        names.update(_PUBLIC_FIGURE_REFERENCES)
    except Exception:  # noqa: BLE001 - the tagged names alone still guard the brief
        pass
    return sorted(names)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def receipt_metrics(receipt: dict[str, Any]) -> tuple[float | None, float | None, str | None]:
    """Lyric error and mastered loudness of the candidate hal_song_pipeline_v1 selected."""
    name = (receipt.get("selection") or {}).get("selected")
    chosen = (receipt.get("candidates") or {}).get(name) or {}
    take_wer = (chosen.get("lyrics") or {}).get("reached_word_error_rate")
    output_i = ((chosen.get("mastering") or {}).get("measurement") or {}).get("output_i")
    try:
        lufs = float(output_i) if output_i not in (None, "") else None
    except (TypeError, ValueError):
        lufs = None
    return take_wer, lufs, name


def load_catalog_vectors(folder: Path = STATE / "analysis") -> dict[str, list[float]]:
    vectors = {}
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("role") == "original" and data.get("style_vector"):
            vectors[data["song_id"]] = data["style_vector"]
    return vectors


# ---------------------------------------------------------------- commands

def cmd_catalog(args: argparse.Namespace) -> int:
    rows = [json.loads(line) for line in Path(args.ytdlp).read_text(encoding="utf-8").splitlines() if line.strip()]
    catalog = build_catalog(rows)
    write_json(Path(args.out), catalog)
    print(json.dumps(catalog["counts"]))
    return 0


def _embedder_and_vocab() -> tuple[MuLanEmbedder, np.ndarray]:
    embedder = MuLanEmbedder()
    return embedder, embedder.embed_texts(STYLE_VOCAB)


def parse_items(single_audio: str | None, single_id: str | None, items: list[str] | None) -> list[tuple[str, Path]]:
    """`--audio X --id Y` or `--items id=path ...`: one model load for a whole batch."""
    pairs = [(single_id, Path(single_audio))] if single_audio and single_id else []
    for item in items or []:
        song_id, sep, path = item.partition("=")
        if not sep or not song_id.strip() or not path.strip():
            raise ValueError(f"expected id=path, got {item!r}")
        pairs.append((song_id.strip(), Path(path.strip())))
    if not pairs:
        raise ValueError("nothing to analyze: pass --audio and --id, or --items id=path")
    return pairs


def cmd_analyze(args: argparse.Namespace, store: Any = None) -> int:
    from hal_gpu_lease import gpu_lease  # noqa: PLC0415

    store = store or event_store()
    pairs = parse_items(args.audio, args.id, args.items)
    with gpu_lease(SOURCE, "style fingerprints and vocal stems", wait_seconds=900):
        embedder, vocab = _embedder_and_vocab()
        for song_id, audio in pairs:
            started = time.time()
            analysis = analyze_audio(audio, embedder, vocab)
            analysis.update({"schema": "hal.our_version.analysis.v1", "song_id": song_id, "role": args.role,
                             "created_at_utc": utc_now(), "context": context_of(analysis)})
            if args.lyrics:
                from hal_lyric_timeline_v1 import transcribe_words  # noqa: PLC0415
                from hal_voice_clone_pipeline import separate  # noqa: PLC0415

                vocals = Path(separate(audio))  # the Demucs vocal stem itself
                analysis["lyrics"] = tag_sections(lyric_lines_from_words(transcribe_words(vocals)))
                analysis["lyrics_source"] = "Whisper on the Demucs vocal stem: the owner's own words, unedited"
            analysis["seconds"] = round(time.time() - started, 1)
            out = write_json(STATE / "analysis" / f"{song_id}.json", analysis)
            record(store, "our_version.analyzed", song_id,
                   {"song_id": song_id, "role": args.role, "sha256": analysis["sha256"],
                    "tempo_bpm": analysis["tempo_bpm"], "key": analysis["key"]["key"], "context": analysis["context"],
                    "style_tags": analysis.get("style_tags", [])[:5]})
            print(out.name, analysis["tempo_bpm"], analysis["key"]["key"], analysis["context"],
                  [tag for tag, _ in analysis.get("style_tags", [])[:5]], flush=True)
    return 0


def cmd_brief(args: argparse.Namespace, store: Any = None) -> int:
    store = store or event_store()
    analysis = json.loads((STATE / "analysis" / f"{args.id}.json").read_text(encoding="utf-8"))
    learner = learner_from_store(store)
    # One seed per song: reproducible, but songs explore different choices while the learner is still empty.
    rng = random.Random(f"{args.seed}:{args.id}") if args.seed is not None else random.Random()
    picked = learner.sample(context_of(analysis), rng)
    lyrics, restoration = analysis.get("lyrics"), None
    if args.restore_lyrics and lyrics:
        from hal_deep_research_v1 import GatewayModel  # noqa: PLC0415

        model = GatewayModel(args.restore_model)
        restoration = restore_lyrics(lyrics, lambda system, user: model.complete(system, user, max_tokens=2500))
        lyrics = restoration["lyrics"]
    brief = build_brief(args.id, analysis, picked, banned_names(), seconds=args.seconds, lyrics=lyrics)
    if restoration is not None:
        brief["lyrics_raw"] = analysis.get("lyrics")
        brief["lyrics_restoration"] = {k: v for k, v in restoration.items() if k != "lyrics"}
    out = write_json(STATE / "briefs" / f"{args.id}_{int(time.time())}.json", brief)
    record(store, "our_version.brief", args.id, {"song_id": args.id, "context": brief["context"],
                                                 "choices": picked, "prompt": brief["prompt"], "file": str(out)})
    print(out)
    print(brief["prompt"])
    return 0


def cmd_score(args: argparse.Namespace, store: Any = None) -> int:
    store = store or event_store()
    original = json.loads((STATE / "analysis" / f"{args.id}.json").read_text(encoding="utf-8"))
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    embedder, vocab = _embedder_and_vocab()
    take = analyze_audio(Path(args.take), embedder, vocab)
    take_wer = lufs = None
    if args.receipt:
        take_wer, lufs, _candidate = receipt_metrics(json.loads(Path(args.receipt).read_text(encoding="utf-8")))
    original_wer = args.original_wer
    style = cosine(original["style_vector"], take["style_vector"])
    rank = catalog_rank(take["style_vector"], args.id, load_catalog_vectors())
    # Loudness counts only for a mastered take (from the pipeline receipt); a raw generation is not mastered yet.
    in_time = None
    if args.fit:  # a remix take: the beat must hold the vocal's timing
        in_time = bool(json.loads(Path(args.fit).read_text(encoding="utf-8")).get("in_time"))
    scored = reward(style, rank, take_wer, original_wer, lufs, in_time)
    result = {"schema": "hal.our_version.score.v1", "song_id": args.id, "take": str(args.take),
              "take_sha256": take["sha256"], "brief": str(args.brief), "context": brief["context"],
              "choices": brief["choices"], "style_similarity": style, "catalog_rank": rank,
              "take_wer": take_wer, "original_wer": original_wer, "take_tags": take.get("style_tags", [])[:6],
              "tempo_bpm": take["tempo_bpm"], "key": take["key"]["key"], "in_time": in_time, "fit": args.fit,
              **scored, "created_at_utc": utc_now()}
    out = write_json(STATE / "scores" / f"{args.id}_{Path(args.take).stem}.json", result)
    record(store, "our_version.reward", LEARNER_SUBJECT,
           {"kind": "reward", "song_id": args.id, "take_sha256": take["sha256"], "context": brief["context"],
            "choices": brief["choices"], "reward": scored["reward"], "weight": 1.0, "pass": scored["pass"]})
    print(out)
    print(json.dumps({k: result[k] for k in ("style_similarity", "catalog_rank", "reward", "pass", "components")}))
    return 0


def cmd_verdict(args: argparse.Namespace, store: Any = None) -> int:
    store = store or event_store()
    score = json.loads(Path(args.score).read_text(encoding="utf-8"))
    keep = bool(args.keep)
    record(store, "our_version.verdict", LEARNER_SUBJECT,
           {"kind": "verdict", "song_id": score["song_id"], "take_sha256": score["take_sha256"],
            "context": score["context"], "choices": score["choices"], "reward": 1.0 if keep else 0.0,
            "weight": 3.0, "by": "owner"})
    print("recorded", "KEEP" if keep else "REJECT", score["song_id"])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("catalog")
    p.add_argument("--ytdlp", required=True)
    p.add_argument("--out", default=str(STATE / "catalog_v1.json"))
    p = sub.add_parser("analyze")
    p.add_argument("--audio")
    p.add_argument("--id")
    p.add_argument("--items", nargs="+", help="id=path pairs, analyzed with one model load")
    p.add_argument("--role", default="original", choices=["original", "take"])
    p.add_argument("--lyrics", action="store_true", help="separate vocals and transcribe the owner's lyrics")
    p = sub.add_parser("brief")
    p.add_argument("--id", required=True)
    p.add_argument("--seconds", type=int, default=180)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--restore-lyrics", action="store_true", help="repair transcription mishearings (guarded)")
    p.add_argument("--restore-model", default="hal/deep")
    p = sub.add_parser("score")
    p.add_argument("--id", required=True)
    p.add_argument("--take", required=True)
    p.add_argument("--brief", required=True)
    p.add_argument("--receipt", default=None, help="hal_song_pipeline_v1 receipt for the take (WER, loudness)")
    p.add_argument("--original-wer", type=float, default=None)
    p.add_argument("--fit", default=None, help="hal_remix_v1 fit JSON for a remix take (timing gate)")
    p = sub.add_parser("verdict")
    p.add_argument("--score", required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--keep", action="store_true")
    group.add_argument("--reject", action="store_true")
    args = parser.parse_args(argv)
    return {"catalog": cmd_catalog, "analyze": cmd_analyze, "brief": cmd_brief, "score": cmd_score,
            "verdict": cmd_verdict}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
