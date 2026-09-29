package com.halsupreme.capture;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

public final class TimelineActivity extends Activity {
    private static final int VIDEO = 8101, MUSIC = 8102;
    private static final int BG = 0xff090a0f, PANEL = 0xff151621, TEXT = 0xfff7f7fb, MUTED = 0xffb1b3c4, MINT = 0xff66f2c2, PURPLE = 0xff8d72ff;
    private final ArrayList<TimelinePlan.Clip> clips = new ArrayList<>();
    private final Handler main = new Handler(Looper.getMainLooper());
    private LinearLayout rows;
    private TextView summary, status, musicLabel, sourceLabel, gainLabel;
    private Spinner format;
    private SeekBar source, music;
    private ProgressBar progress;
    private VideoView preview;
    private Button export, cancel;
    private String musicUri;
    private Uri lastExport;
    private TimelineExporter exporter;
    private boolean busy, importing;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this); scroll.setBackgroundColor(BG);
        scroll.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(0,i.getSystemWindowInsetTop(),0,i.getSystemWindowInsetBottom());return i;});
        LinearLayout root = column(); root.setPadding(dp(18),dp(20),dp(18),dp(32)); scroll.addView(root); setContentView(scroll);
        root.addView(text("HAL CAPTURE / STUDIO 0.4",12,PURPLE,true));
        root.addView(text("Your story.\nIn sequence.",30,TEXT,true));
        root.addView(text("Local-first multi-clip editing. Import, arrange, mix and export a new MP4. Original files stay unchanged.",14,MUTED,false));
        LinearLayout actions = row(); root.addView(actions,space());
        addButton(actions,"ADD VIDEOS",()->pick(VIDEO),true);
        addButton(actions,"ADD LATEST",this::addLatest,true);
        summary=text("0 clips",13,MINT,true); root.addView(summary,space());
        rows=column(); root.addView(rows);
        root.addView(text("Clips play end-to-end with hard cuts. Tap Trim to set each clip's in/out points.",12,MUTED,false),space());
        LinearLayout audio=card(); root.addView(audio,space());
        audio.addView(text("SOUNDTRACK",12,PURPLE,true));
        musicLabel=text("No music selected",13,MUTED,false);audio.addView(musicLabel);
        LinearLayout ma=row();audio.addView(ma,space());addButton(ma,"IMPORT MUSIC",()->pick(MUSIC),true);addButton(ma,"REMOVE MUSIC",()->{if(!editable())return;musicUri=null;refresh();},true);
        sourceLabel=text("Source audio 80%",13,TEXT,false); audio.addView(sourceLabel);
        source=level(80);source.setContentDescription("Source audio level");audio.addView(source);
        gainLabel=text("Music 20%",13,TEXT,false);audio.addView(gainLabel);
        music=level(20);music.setContentDescription("Music level");audio.addView(music);
        SeekBar.OnSeekBarChangeListener change = new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int p,boolean u){sourceLabel.setText("Source audio "+source.getProgress()+"%");gainLabel.setText("Music "+music.getProgress()+"%");}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){saveDraft();}};
        source.setOnSeekBarChangeListener(change);music.setOnSeekBarChangeListener(change);
        audio.addView(text("Music loops to the video length. Automatic headroom reduces overload when both levels are high. Only import audio you have rights to use.",12,MUTED,false));
        LinearLayout delivery=card();root.addView(delivery,space());delivery.addView(text("DELIVERY",12,PURPLE,true));
        format=new Spinner(this); ArrayAdapter<String> a=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,new String[]{"YouTube 16:9 / 720p","Shorts 9:16 / 720p","Square 1:1 / 720p"});a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);format.setAdapter(a);delivery.addView(format,new LinearLayout.LayoutParams(-1,dp(52)));
        delivery.addView(text("Fit framing preserves the whole image; black bars may be added. H.264 video + AAC audio. Keep this screen open while rendering.",12,MUTED,false));
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);delivery.addView(progress,new LinearLayout.LayoutParams(-1,dp(12)));
        status=text("Ready when you are",13,MINT,true);delivery.addView(status,space());
        export=button("EXPORT TIMELINE",MINT);export.setTextColor(BG);export.setOnClickListener(v->render());delivery.addView(export,new LinearLayout.LayoutParams(-1,dp(54)));
        cancel=button("CANCEL EXPORT",PANEL);cancel.setVisibility(View.GONE);cancel.setOnClickListener(v->cancelRender());delivery.addView(cancel,new LinearLayout.LayoutParams(-1,dp(48)));
        preview=new VideoView(this);delivery.addView(preview,new LinearLayout.LayoutParams(-1,dp(190)));
        LinearLayout result=row();delivery.addView(result,space());addButton(result,"PLAY EXPORT",()->{if(lastExport==null){say("Export a project first");return;}preview.setVideoURI(lastExport);preview.start();},true);addButton(result,"SHARE EXPORT",()->{if(lastExport!=null)ShareUtils.share(this,lastExport,false);else say("Export a project first");},true);
        LinearLayout draft=row();root.addView(draft,space());addButton(draft,"SAVE DRAFT",()->{saveDraft();say("Draft saved on this phone");},true);addButton(draft,"NEW PROJECT",()->{if(!editable())return;new AlertDialog.Builder(this).setTitle("Clear this timeline?").setMessage("Only the draft is cleared. Original media and exports are kept.").setPositiveButton("Clear",(d,w)->{clips.clear();musicUri=null;refresh();}).setNegativeButton("Cancel",null).show();},true);
        Button back=button("BACK TO CAPTURE",PANEL);back.setOnClickListener(v->finish());root.addView(back,space());
        restoreDraft();refresh();
    }
    private boolean editable(){if(busy||importing){say("Finish the current operation first");return false;}return true;}
    private void pick(int code){if(!editable())return;Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(code==VIDEO?"video/*":"audio/*").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);if(code==VIDEO)i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);try{startActivityForResult(i,code);}catch(Exception e){say("No file picker available");}}
    @Override protected void onActivityResult(int code,int result,Intent data){super.onActivityResult(code,result,data);if(result!=RESULT_OK||data==null)return;List<Uri> selected=new ArrayList<>();if(data.getClipData()!=null){for(int n=0;n<data.getClipData().getItemCount();n++)selected.add(data.getClipData().getItemAt(n).getUri());}else if(data.getData()!=null)selected.add(data.getData());for(Uri uri:selected){try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}}importUris(selected,code==MUSIC);}
    private void addLatest(){if(!editable())return;String s=getSharedPreferences(RecordingService.PREFS,MODE_PRIVATE).getString(RecordingService.KEY_LATEST_URI,null);if(s==null){say("Make a recording first, or use Add Videos");return;}importUris(Collections.singletonList(Uri.parse(s)),false);}
    private void importUris(List<Uri> uris,boolean soundtrack){
        if(uris.isEmpty())return;
        if(!soundtrack&&clips.size()+uris.size()>TimelinePlan.MAX_CLIPS){say("Maximum 20 clips per project");return;}
        importing=true;status.setText("Reading local media...");
        new Thread(()->{ArrayList<TimelinePlan.Clip> read=new ArrayList<>();String failure=null;try{for(Uri uri:uris){if(!"content".equals(uri.getScheme()))throw new IllegalArgumentException("Select local content with the file picker");MediaMetadataRetriever r=new MediaMetadataRetriever();try{r.setDataSource(this,uri);String has=r.extractMetadata(soundtrack?MediaMetadataRetriever.METADATA_KEY_HAS_AUDIO:MediaMetadataRetriever.METADATA_KEY_HAS_VIDEO);if(!"yes".equals(has))throw new IllegalArgumentException("Selected file lacks the required media track");long duration=Long.parseLong(r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION));String name=soundtrack?"Imported soundtrack":"Video "+(clips.size()+read.size()+1);read.add(new TimelinePlan.Clip(uri.toString(),name,duration,0,duration));}finally{r.release();}}}catch(Exception e){failure=e.getMessage();}final String error=failure;main.post(()->{importing=false;if(isDestroyed())return;if(error!=null){status.setText("Import failed");say(error);return;}if(soundtrack)musicUri=read.get(0).uri;else clips.addAll(read);status.setText("Media added");refresh();});},"hal-import").start();
    }
    private void refresh(){
        if(rows==null)return;rows.removeAllViews();long duration=0;for(TimelinePlan.Clip c:clips)duration+=c.lengthMs();summary.setText(String.format(Locale.US,"%d CLIPS  /  %.1f SECONDS  /  ON DEVICE",clips.size(),duration/1000f));musicLabel.setText(musicUri==null?"No music selected":"Soundtrack loaded / loops to project length");
        for(int n=0;n<clips.size();n++){final int index=n;TimelinePlan.Clip c=clips.get(n);LinearLayout item=card();item.addView(text(String.format(Locale.US,"%02d   %s",n+1,c.name),15,TEXT,true));item.addView(text(String.format(Locale.US,"%.1fs - %.1fs  /  %.1fs",c.startMs/1000f,c.endMs/1000f,c.lengthMs()/1000f),12,MUTED,false));LinearLayout tools=row();item.addView(tools,space());addButton(tools,"TRIM",()->trim(index),true);addButton(tools,"UP",()->{if(!editable()||index==0)return;Collections.swap(clips,index,index-1);refresh();},true);addButton(tools,"REMOVE",()->{if(!editable())return;clips.remove(index);refresh();},true);rows.addView(item,space());}
        saveDraft();
    }
    private void trim(int n){if(!editable())return;TimelinePlan.Clip c=clips.get(n);LinearLayout box=column();box.setPadding(dp(20),dp(12),dp(20),dp(12));EditText from=new EditText(this),to=new EditText(this);from.setInputType(8194);to.setInputType(8194);from.setHint("Start seconds");to.setHint("End seconds");from.setText(String.format(Locale.US,"%.3f",c.startMs/1000d));to.setText(String.format(Locale.US,"%.3f",c.endMs/1000d));box.addView(text("Start / end seconds",14,TEXT,true));box.addView(from);box.addView(to);AlertDialog d=new AlertDialog.Builder(this).setTitle("Trim clip "+(n+1)).setView(box).setPositiveButton("Apply",null).setNegativeButton("Cancel",null).create();d.setOnShowListener(x->d.getButton(-1).setOnClickListener(v->{try{double f=Double.parseDouble(from.getText().toString()),t=Double.parseDouble(to.getText().toString());if(!Double.isFinite(f)||!Double.isFinite(t))throw new IllegalArgumentException("Use finite seconds");clips.set(n,new TimelinePlan.Clip(c.uri,c.name,c.durationMs,Math.round(f*1000),Math.round(t*1000)));refresh();d.dismiss();}catch(Exception e){say("Invalid trim: "+e.getMessage());}}));d.show();}
    private void render(){if(!editable())return;try{TimelinePlan p=new TimelinePlan(clips,musicUri,source.getProgress()/100f,music.getProgress()/100f,format.getSelectedItemPosition());saveDraft();busy=true;export.setEnabled(false);cancel.setVisibility(View.VISIBLE);preview.stopPlayback();status.setText("Preparing composition...");exporter=new TimelineExporter(this);exporter.start(p,new TimelineExporter.Listener(){public void saved(Uri uri){busy=false;lastExport=uri;getSharedPreferences(RecordingService.PREFS,MODE_PRIVATE).edit().putString(RecordingService.KEY_LATEST_URI,uri.toString()).apply();export.setEnabled(true);cancel.setVisibility(View.GONE);progress.setIndeterminate(false);progress.setProgress(100);status.setText("Export saved / Movies/HAL Capture/Edits");preview.setVideoURI(uri);preview.start();}public void failed(String e){busy=false;export.setEnabled(true);cancel.setVisibility(View.GONE);progress.setIndeterminate(false);status.setText(e);}});poll();}catch(Exception e){say(e.getMessage());}}
    private void poll(){if(!busy)return;int p=exporter.progress();progress.setIndeterminate(p<0);if(p>=0)progress.setProgress(p);status.setText(p<0?"Preparing render...":"Rendering "+p+"%");main.postDelayed(this::poll,500);}
    private void cancelRender(){if(exporter!=null)exporter.cancel();busy=false;export.setEnabled(true);cancel.setVisibility(View.GONE);progress.setIndeterminate(false);progress.setProgress(0);status.setText("Export cancelled / original files kept");}
    private void saveDraft(){if(format==null)return;try{JSONArray items=new JSONArray();for(TimelinePlan.Clip c:clips)items.put(new JSONObject().put("uri",c.uri).put("name",c.name).put("duration",c.durationMs).put("start",c.startMs).put("end",c.endMs));JSONObject d=new JSONObject().put("clips",items).put("music",musicUri==null?JSONObject.NULL:musicUri).put("sourceGain",source.getProgress()).put("musicGain",music.getProgress()).put("format",format.getSelectedItemPosition());getSharedPreferences("hal_timeline",MODE_PRIVATE).edit().putString("draft",d.toString()).apply();}catch(Exception e){say("Draft could not be saved");}}
    private void restoreDraft(){String raw=getSharedPreferences("hal_timeline",MODE_PRIVATE).getString("draft",null);if(raw==null)return;try{JSONObject d=new JSONObject(raw);JSONArray a=d.getJSONArray("clips");if(a.length()>20)throw new IllegalArgumentException();for(int n=0;n<a.length();n++){JSONObject c=a.getJSONObject(n);clips.add(new TimelinePlan.Clip(c.getString("uri"),c.getString("name"),c.getLong("duration"),c.getLong("start"),c.getLong("end")));}musicUri=d.isNull("music")?null:d.getString("music");source.setProgress(d.optInt("sourceGain",80));music.setProgress(d.optInt("musicGain",20));format.setSelection(Math.max(0,Math.min(2,d.optInt("format",0))));}catch(Exception e){clips.clear();musicUri=null;say("Old draft unavailable; original media is unchanged");}}
    @Override protected void onPause(){super.onPause();saveDraft();preview.pause();}
    @Override protected void onDestroy(){main.removeCallbacksAndMessages(null);if(busy&&exporter!=null)exporter.cancel();super.onDestroy();}
    private void say(String s){Toast.makeText(this,s==null?"Operation unavailable":s,Toast.LENGTH_LONG).show();}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(1);return l;}
    private LinearLayout row(){LinearLayout l=new LinearLayout(this);l.setOrientation(0);return l;}
    private TextView text(String s,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);t.setPadding(0,dp(4),0,dp(4));if(bold)t.setTypeface(null,Typeface.BOLD);return t;}
    private GradientDrawable background(int color){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(16));return d;}
    private LinearLayout card(){LinearLayout l=column();l.setPadding(dp(14),dp(14),dp(14),dp(14));l.setBackground(background(PANEL));return l;}
    private Button button(String s,int color){Button b=new Button(this);b.setText(s);b.setTextSize(11);b.setTextColor(TEXT);b.setAllCaps(false);b.setBackground(background(color));b.setContentDescription(s);return b;}
    private void addButton(LinearLayout l,String s,Runnable run,boolean weight){Button b=button(s,0xff29283d);b.setOnClickListener(v->run.run());LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(weight?0:-1,dp(48),weight?1:0);p.setMargins(dp(2),0,dp(2),0);l.addView(b,p);}
    private LinearLayout.LayoutParams space(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(12);return p;}
    private SeekBar level(int value){SeekBar s=new SeekBar(this);s.setMax(100);s.setProgress(value);return s;}
}
