package com.halsupreme.capture;
import org.junit.Test;
import java.util.*;
import static org.junit.Assert.*;

public class TimelinePlanTest {
    private TimelinePlan.Clip clip(){return new TimelinePlan.Clip("content://media/video/1","First",10000,1000,5000);}
    private TimelinePlan plan(List<TimelinePlan.Clip> clips){return new TimelinePlan(clips,null,.8f,.2f,0);}
    @Test public void durationUsesTrimmedRange(){assertEquals(8000,plan(Arrays.asList(clip(),clip())).durationMs);}
    @Test public void snapshotIsDefensive(){List<TimelinePlan.Clip> c=new ArrayList<>();c.add(clip());TimelinePlan p=plan(c);c.clear();assertEquals(1,p.clips.size());assertThrows(UnsupportedOperationException.class,()->p.clips.clear());}
    @Test public void emptyRejected(){assertThrows(IllegalArgumentException.class,()->plan(Collections.emptyList()));}
    @Test public void nullClipRejected(){assertThrows(IllegalArgumentException.class,()->plan(Collections.singletonList(null)));}
    @Test public void maximumTwenty(){assertEquals(20,plan(Collections.nCopies(20,clip())).clips.size());assertThrows(IllegalArgumentException.class,()->plan(Collections.nCopies(21,clip())));}
    @Test public void negativeTrimRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan.Clip("content://a","a",100,-1,50));}
    @Test public void reversedTrimRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan.Clip("content://a","a",100,60,50));}
    @Test public void zeroLengthRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan.Clip("content://a","a",100,50,50));}
    @Test public void overrunRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan.Clip("content://a","a",100,0,101));}
    @Test public void networkSourcesRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan.Clip("https://example.test/a","a",100,0,50));}
    @Test public void musicMustBeLocal(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan(Arrays.asList(clip()),"https://example.test/a",1,1,0));}
    @Test public void invalidGainsRejected(){for(float g:new float[]{Float.NaN,Float.POSITIVE_INFINITY,-.01f,1.01f})assertThrows(IllegalArgumentException.class,()->new TimelinePlan(Arrays.asList(clip()),null,g,.2f,0));}
    @Test public void combinedAudioHasHeadroom(){TimelinePlan p=new TimelinePlan(Arrays.asList(clip()),"content://media/audio/2",1,1,1);assertEquals(.5f,p.gainScale(),.0001f);}
    @Test public void noMusicDoesNotAttenuateSource(){assertEquals(1f,new TimelinePlan(Arrays.asList(clip()),null,1,1,0).gainScale(),.0001f);}
    @Test public void framesMatchPreset(){for(int i=0;i<3;i++){TimelinePlan p=new TimelinePlan(Arrays.asList(clip()),null,1,0,i);assertEquals(i==0?1280:720,p.width());assertEquals(i==1?1280:720,p.height());}}
    @Test public void invalidPresetRejected(){assertThrows(IllegalArgumentException.class,()->new TimelinePlan(Arrays.asList(clip()),null,1,0,3));}
    @Test public void keepsClipOrder(){TimelinePlan.Clip b=new TimelinePlan.Clip("content://media/video/2","second",9000,0,7000);TimelinePlan p=plan(Arrays.asList(b,clip()));assertEquals("second",p.clips.get(0).name);assertEquals(11000,p.durationMs);}
    @Test public void longProjectsRejected(){TimelinePlan.Clip c=new TimelinePlan.Clip("content://media/video/2","long",TimelinePlan.MAX_DURATION_MS+1,0,TimelinePlan.MAX_DURATION_MS+1);assertThrows(IllegalArgumentException.class,()->plan(Arrays.asList(c)));}
}
