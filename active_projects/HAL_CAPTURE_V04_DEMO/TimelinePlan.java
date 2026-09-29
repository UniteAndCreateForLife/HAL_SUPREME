package com.halsupreme.capture;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Android-free, immutable export input. Editing never changes a running job. */
public final class TimelinePlan {
    public static final int MAX_CLIPS = 20;
    public static final long MAX_DURATION_MS = 4 * 60 * 60 * 1000L;
    public static final class Clip {
        public final String uri, name;
        public final long durationMs, startMs, endMs;
        public Clip(String uri, String name, long durationMs, long startMs, long endMs) {
            if (uri == null || !uri.startsWith("content://")) throw new IllegalArgumentException("Choose a local media file using the file picker.");
            if (durationMs <= 0 || startMs < 0 || endMs <= startMs || endMs > durationMs)
                throw new IllegalArgumentException("Trim must be inside the clip, with End after Start.");
            this.uri = uri; this.name = name == null ? "Clip" : name;
            this.durationMs = durationMs; this.startMs = startMs; this.endMs = endMs;
        }
        public long lengthMs() { return endMs - startMs; }
    }
    public final List<Clip> clips;
    public final String musicUri;
    public final float sourceGain, musicGain;
    public final int format;
    public final long durationMs;
    public TimelinePlan(List<Clip> clips, String musicUri, float sourceGain, float musicGain, int format) {
        if (clips == null || clips.isEmpty() || clips.size() > MAX_CLIPS)
            throw new IllegalArgumentException("Choose between 1 and 20 video clips.");
        if (!Float.isFinite(sourceGain) || !Float.isFinite(musicGain) || sourceGain < 0 || sourceGain > 1 || musicGain < 0 || musicGain > 1)
            throw new IllegalArgumentException("Audio levels must be between 0 and 100%.");
        if (format < 0 || format > 2) throw new IllegalArgumentException("Choose an export format.");
        if (musicUri != null && !musicUri.startsWith("content://")) throw new IllegalArgumentException("Choose music using the file picker.");
        long total = 0;
        for (Clip c : clips) {
            if (c == null) throw new IllegalArgumentException("A clip is missing.");
            total = Math.addExact(total, c.lengthMs());
        }
        if (total > MAX_DURATION_MS) throw new IllegalArgumentException("Export is limited to four hours in this alpha.");
        this.clips = Collections.unmodifiableList(new ArrayList<>(clips));
        this.musicUri = musicUri; this.sourceGain = sourceGain; this.musicGain = musicGain;
        this.format = format; this.durationMs = total;
    }
    public int width() { return format == 0 ? 1280 : 720; }
    public int height() { return format == 1 ? 1280 : 720; }
    /** Reserve headroom rather than clipping when both inputs are at full volume. */
    public float gainScale() { return 1f / Math.max(1f, sourceGain + (musicUri == null ? 0 : musicGain)); }
}
