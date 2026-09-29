package com.halsupreme.capture.playbackfixture;

import android.app.Activity;
import android.os.Bundle;
import android.os.SystemClock;
import android.graphics.*;
import android.view.View;
import android.widget.*;
import android.media.*;

/** Original test content, in a separate APK, not a production capture backdoor. */
public final class PlaybackActivity extends Activity {
    private AudioTrack tone;
    private volatile boolean playing;
    private Thread worker;
    private long start;
    @Override public void onCreate(Bundle b){
        super.onCreate(b);start=SystemClock.elapsedRealtime();
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xff080b15);root.setPadding(24,48,24,28);
        TextView title=new TextView(this);title.setText("HAL / TEST SIGNAL");title.setTextColor(0xff78f5d2);title.setTextSize(24);root.addView(title);
        TextView detail=new TextView(this);detail.setText("Original animated fixture • separate Android app\nPublic playback-capture API enabled\nDigital audio test, not microphone validation");detail.setTextColor(0xffccccdd);detail.setTextSize(14);root.addView(detail);
        root.addView(new SignalView(),new LinearLayout.LayoutParams(-1,0,1));
        Button play=new Button(this);play.setText("PLAY TEST SIGNAL");play.setOnClickListener(v->startTone());root.addView(play);
        Button stop=new Button(this);stop.setText("STOP TEST SIGNAL");stop.setOnClickListener(v->stopTone());root.addView(stop);
        setContentView(root);
    }
    private void startTone(){
        if(playing)return;
        AudioAttributes attr=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).setAllowedCapturePolicy(AudioAttributes.ALLOW_CAPTURE_BY_ALL).build();
        AudioFormat fmt=new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).build();
        tone=new AudioTrack.Builder().setAudioAttributes(attr).setAudioFormat(fmt).setTransferMode(AudioTrack.MODE_STREAM).setBufferSizeInBytes(19200).build();
        if(tone.getState()!=AudioTrack.STATE_INITIALIZED){tone.release();tone=null;return;}
        playing=true;tone.play();
        worker=new Thread(()->{long sample=0;short[] pcm=new short[1920];while(playing){for(int n=0;n<960;n++){double t=(sample++)/48000d;double env=.45+.35*Math.sin(2*Math.PI*.5*t);short v=(short)(4500*env*(Math.sin(2*Math.PI*440*t)+.3*Math.sin(2*Math.PI*660*t)));pcm[n*2]=v;pcm[n*2+1]=v;}AudioTrack current=tone;if(current==null)break;int written=current.write(pcm,0,pcm.length,AudioTrack.WRITE_BLOCKING);if(written<0)break;}},"hal-test-tone");worker.start();
    }
    private void stopTone(){playing=false;AudioTrack t=tone;if(t!=null){try{t.pause();t.flush();}catch(IllegalStateException ignored){}}if(worker!=null){try{worker.join(1000);}catch(InterruptedException e){Thread.currentThread().interrupt();}}if(t!=null)t.release();tone=null;}
    @Override protected void onPause(){stopTone();super.onPause();}
    private final class SignalView extends View {
        private final Paint p=new Paint(3);
        SignalView(){super(PlaybackActivity.this);setContentDescription("Moving video calibration pattern");}
        @Override public void onDraw(Canvas c){
            float w=getWidth(),h=getHeight(),t=(SystemClock.elapsedRealtime()-start)/1000f;
            c.drawColor(0xff080b15);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1);p.setColor(0xff20253d);
            for(int x=0;x<w;x+=48)c.drawLine(x,0,x,h,p);for(int y=0;y<h;y+=48)c.drawLine(0,y,w,y,p);
            c.save();c.translate(w/2,h*.45f);c.rotate(t*25);p.setStrokeWidth(5);p.setColor(0xff9879ff);c.drawRoundRect(-w*.28f,-w*.28f,w*.28f,w*.28f,24,24,p);p.setColor(0xff66f2c2);c.drawCircle(0,0,w*.18f*(1+.1f*(float)Math.sin(t*3)),p);c.restore();
            p.setStyle(Paint.Style.FILL);p.setColor(0xff66f2c2);c.drawCircle(w*.5f+w*.35f*(float)Math.sin(t*1.3f),h*.45f+h*.22f*(float)Math.cos(t*.9f),16,p);
            p.setTextAlign(Paint.Align.CENTER);p.setColor(Color.WHITE);p.setTextSize(40);p.setTypeface(Typeface.MONOSPACE);c.drawText(String.format(java.util.Locale.US,"%05.1f s",t),w/2,h*.79f,p);
            p.setTextSize(22);p.setColor(playing?0xff66f2c2:0xffa9adc5);c.drawText(playing?"440 + 660 Hz / PLAYING":"PRESS PLAY FOR AUDIO",w/2,h*.87f,p);
            postInvalidateDelayed(33);
        }
    }
}
