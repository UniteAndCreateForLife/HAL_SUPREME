package com.halsupreme.capture;

import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import androidx.annotation.OptIn;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.audio.AudioProcessor;
import androidx.media3.common.audio.BaseAudioProcessor;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.effect.Presentation;
import androidx.media3.transformer.Composition;
import androidx.media3.transformer.EditedMediaItem;
import androidx.media3.transformer.EditedMediaItemSequence;
import androidx.media3.transformer.Effects;
import androidx.media3.transformer.ExportException;
import androidx.media3.transformer.ExportResult;
import androidx.media3.transformer.ProgressHolder;
import androidx.media3.transformer.Transformer;
import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** One exporter per immutable project snapshot; all public calls are main-thread calls. */
@OptIn(markerClass = UnstableApi.class)
public final class TimelineExporter {
    public interface Listener { void saved(Uri uri); void failed(String error); }
    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private Transformer transformer;
    private volatile boolean cancelled;
    private volatile boolean copying;
    private File output;
    public TimelineExporter(Context context) { this.context = context.getApplicationContext(); }
    public void start(TimelinePlan plan, Listener listener) {
        if (transformer != null) throw new IllegalStateException("Create a new exporter for each job.");
        try {
            File dir = new File(context.getCacheDir(), "timeline_exports");
            if (!dir.isDirectory() && !dir.mkdirs()) throw new IllegalStateException("Export storage unavailable");
            long reserve = 128L * 1024 * 1024 + plan.durationMs * 1400L;
            if (dir.getUsableSpace() < reserve) throw new IllegalStateException("Not enough free space for this export and save copy");
            output = File.createTempFile("HAL_timeline_", ".mp4", dir);
            if (!output.delete()) throw new IllegalStateException("Could not prepare export file");
            List<EditedMediaItem> items = new ArrayList<>();
            for (TimelinePlan.Clip c : plan.clips) {
                MediaItem item = new MediaItem.Builder().setUri(Uri.parse(c.uri))
                    .setClippingConfiguration(new MediaItem.ClippingConfiguration.Builder()
                        .setStartPositionMs(c.startMs).setEndPositionMs(c.endMs).build()).build();
                Effects effects = new Effects(Collections.singletonList(new Gain(plan.sourceGain * plan.gainScale())),
                    Collections.singletonList(Presentation.createForWidthAndHeight(plan.width(), plan.height(), Presentation.LAYOUT_SCALE_TO_FIT)));
                items.add(new EditedMediaItem.Builder(item).setFrameRate(30).setEffects(effects).build());
            }
            List<EditedMediaItemSequence> sequences = new ArrayList<>();
            sequences.add(new EditedMediaItemSequence.Builder(new java.util.HashSet<>(Arrays.asList(C.TRACK_TYPE_VIDEO, C.TRACK_TYPE_AUDIO)))
                .addItems(items).build());
            if (plan.musicUri != null) {
                EditedMediaItem music = new EditedMediaItem.Builder(MediaItem.fromUri(plan.musicUri))
                    .setRemoveVideo(true)
                    .setEffects(new Effects(Collections.singletonList(new Gain(plan.musicGain * plan.gainScale())), Collections.emptyList())).build();
                sequences.add(new EditedMediaItemSequence.Builder(Collections.singleton(C.TRACK_TYPE_AUDIO))
                    .addItem(music).setIsLooping(true).build());
            }
            Composition composition = new Composition.Builder(sequences).build();
            transformer = new Transformer.Builder(context)
                .setVideoMimeType("video/avc").setAudioMimeType("audio/mp4a-latm")
                .addListener(new Transformer.Listener() {
                    @Override public void onCompleted(Composition composition, ExportResult result) {
                        copying = true;
                        new Thread(() -> {
                            Uri saved = null;
                            try {
                                saved = publish(output);
                                final Uri published = saved;
                                main.post(() -> {
                                    if (cancelled) context.getContentResolver().delete(published, null, null);
                                    else listener.saved(published);
                                });
                            } catch (Exception error) {
                                if (!cancelled) main.post(() -> listener.failed("Save failed: " + error.getClass().getSimpleName()));
                            } finally { copying = false; cleanup(); }
                        }, "hal-timeline-save").start();
                    }
                    @Override public void onError(Composition composition, ExportResult result, ExportException error) {
                        cleanup();
                        if (!cancelled) listener.failed("Export failed: " + error.getErrorCodeName());
                    }
                }).build();
            transformer.start(composition, output.getAbsolutePath());
        } catch (Exception error) {
            cleanup(); listener.failed("Could not export: " + error.getMessage());
        }
    }
    public int progress() {
        if (copying) return 99;
        if (transformer == null || cancelled) return -1;
        ProgressHolder holder = new ProgressHolder();
        return transformer.getProgress(holder) == Transformer.PROGRESS_STATE_AVAILABLE ? holder.progress : -1;
    }
    public void cancel() { cancelled = true; if (transformer != null) transformer.cancel(); if (!copying) cleanup(); }
    private void cleanup() { if (output != null && output.exists() && !output.delete()) android.util.Log.w("HALTimeline", "Temporary export cleanup deferred"); }
    private Uri publish(File file) throws Exception {
        if (file == null || !file.isFile() || file.length() == 0) throw new IllegalStateException("No encoded output");
        ContentValues values = new ContentValues();
        values.put(MediaStore.Video.Media.DISPLAY_NAME, "HAL_Timeline_" + System.currentTimeMillis() + ".mp4");
        values.put(MediaStore.Video.Media.MIME_TYPE, "video/mp4");
        values.put(MediaStore.Video.Media.RELATIVE_PATH, Environment.DIRECTORY_MOVIES + "/HAL Capture/Edits");
        values.put(MediaStore.Video.Media.IS_PENDING, 1);
        Uri uri = context.getContentResolver().insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IllegalStateException("MediaStore unavailable");
        try {
            try (FileInputStream in = new FileInputStream(file); OutputStream out = context.getContentResolver().openOutputStream(uri)) {
                if (out == null) throw new IllegalStateException("Storage unavailable");
                byte[] buffer = new byte[65536]; int count;
                while ((count = in.read(buffer)) != -1) {
                    if (cancelled) throw new InterruptedException("Cancelled");
                    out.write(buffer, 0, count);
                }
            }
            if (cancelled) throw new InterruptedException("Cancelled");
            values.clear(); values.put(MediaStore.Video.Media.IS_PENDING, 0);
            context.getContentResolver().update(uri, values, null, null);
            return uri;
        } catch (Exception error) { context.getContentResolver().delete(uri, null, null); throw error; }
    }
    private static final class Gain extends BaseAudioProcessor {
        private final float gain;
        Gain(float gain) { this.gain = gain; }
        @Override protected AudioFormat onConfigure(AudioFormat format) throws UnhandledAudioFormatException {
            if (format.encoding != C.ENCODING_PCM_16BIT && format.encoding != C.ENCODING_PCM_FLOAT)
                throw new UnhandledAudioFormatException(format);
            return format;
        }
        @Override public void queueInput(ByteBuffer in) {
            ByteBuffer out = replaceOutputBuffer(in.remaining());
            in.order(ByteOrder.nativeOrder()); out.order(ByteOrder.nativeOrder());
            if (inputAudioFormat.encoding == C.ENCODING_PCM_FLOAT) {
                while (in.hasRemaining()) out.putFloat(Math.max(-1f, Math.min(1f, in.getFloat() * gain)));
            } else {
                while (in.hasRemaining()) out.putShort((short)Math.max(-32768, Math.min(32767, Math.round(in.getShort() * gain))));
            }
            out.flip();
        }
    }
}
