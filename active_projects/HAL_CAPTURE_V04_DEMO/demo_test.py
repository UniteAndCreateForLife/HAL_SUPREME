#!/usr/bin/env python3
"""Actual UI-driven Android smoke tests. Never simulates a successful capture/export."""
from pathlib import Path
import subprocess, time, json, re, shlex, xml.etree.ElementTree as ET, traceback, os

OUT=Path('demo-evidence'); OUT.mkdir(exist_ok=True)
APP='com.halsupreme.capture'
LAB=APP+'.playbackfixture'
START=time.monotonic()
EVENTS=[]; CHECKS=[]

def run(args, timeout=30, check=True):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if check and p.returncode: raise RuntimeError(p.stderr.decode(errors='replace')[-2000:])
    return p

def adb(*args,timeout=30,check=True):return run(['adb',*map(str,args)],timeout,check).stdout.decode(errors='replace').strip()
def shell(s,timeout=30,check=True):return adb('shell',s,timeout=timeout,check=check)
def event(name):
    e={'time_seconds':round(time.monotonic()-START,2),'event':name};EVENTS.append(e);print(json.dumps(e),flush=True)
def screenshot(name):
    data=run(['adb','exec-out','screencap','-p']).stdout
    (OUT/(name+'.png')).write_bytes(data)
    event('screenshot:'+name)
def tree():
    adb('shell','uiautomator','dump','/sdcard/hal-window.xml',timeout=25,check=False)
    raw=adb('exec-out','cat','/sdcard/hal-window.xml')
    (OUT/'last-window.xml').write_text(raw)
    return ET.fromstring(raw)
def bounds(node):return list(map(int,re.findall(r'\d+',node.get('bounds',''))))
def tap_node(n):
    x1,y1,x2,y2=bounds(n);adb('shell','input','tap',(x1+x2)//2,(y1+y2)//2);time.sleep(.5)
def nodes_match(t, text):
    return [n for n in t.iter('node') if (text.lower() in n.get('text','').lower() or text.lower() in n.get('content-desc','').lower()) and len(bounds(n))==4 and bounds(n)[3]>bounds(n)[1]]
def tap(text,scroll=False,exact=False):
    for attempt in range(9 if scroll else 1):
        t=tree(); ns=nodes_match(t,text)
        if exact:ns=[n for n in ns if n.get('text','').lower()==text.lower() or n.get('content-desc','').lower()==text.lower()]
        if ns:tap_node(ns[0]);return
        if scroll:adb('shell','input','swipe',360,1070,360,390,300);time.sleep(.4)
    screenshot('missing_'+re.sub(r'\W','_',text)[:30]);raise RuntimeError('UI control not found: '+text)
def maybe(*texts):
    t=tree()
    for text in texts:
        ns=nodes_match(t,text)
        if ns:tap_node(ns[0]);return True
    return False

def top():
    for _ in range(7):adb('shell','input','swipe',360,390,360,1080,150)
    time.sleep(.5)
def prefs():
    raw=adb('shell','run-as',APP,'cat','shared_prefs/hal_capture_state.xml',check=False)
    try:return {n.get('name'):n.get('value',n.text or '') for n in ET.fromstring(raw)}
    except ET.ParseError:return {}
def wait_pref(key,value,seconds=30):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if prefs().get(key)==value:return
        time.sleep(.5)
    raise RuntimeError(f'Expected {key}={value}; got {prefs()}')
def check(name,condition,detail=''):
    CHECKS.append({'check':name,'passed':bool(condition),'detail':detail});event(name+':'+str(bool(condition)))
    if not condition:raise AssertionError(name+': '+detail)
def list_media():
    return set(x for x in shell("find '/sdcard/Movies/HAL Capture' -type f",check=False).splitlines() if x.endswith('.mp4'))
def pull_new(before,label,seconds=120):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        paths=list_media()-before
        if paths:
            src=sorted(paths)[-1];dest=OUT/(label+'.mp4');adb('pull',src,str(dest));return dest
        time.sleep(2)
    raise RuntimeError('No saved MP4 for '+label)
def probe(path):
    d=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout)
    (OUT/(path.stem+'-probe.json')).write_text(json.dumps(d,indent=2))
    return d

def start_activity(component):adb('shell','am','start','-n',component);time.sleep(1.2)
def type_text(value):adb('shell','input','text',shlex.quote(value.replace(' ','%s')));time.sleep(.4)
def edit_field(node,value):
    tap_node(node);adb('shell','input','keyevent','KEYCODE_MOVE_END')
    # Fields here contain short numeric values, never a password.
    for _ in range(16):adb('shell','input','keyevent','KEYCODE_DEL')
    type_text(value)
def wait_text(text,seconds=120):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        t=tree()
        if nodes_match(t,text):return
        errors=[n.get('text','') for n in t.iter('node') if 'failed' in n.get('text','').lower()]
        if errors:raise RuntimeError('; '.join(errors))
        time.sleep(2)
    raise RuntimeError('Timed out waiting for '+text)

def recorder_test():
    event('recorder_start')
    start_activity(APP+'/.MainActivity')
    screenshot('01_capture_home')
    tap('Record microphone',scroll=True,exact=True)  # Off: emulator digital-audio test only.
    top();tap('START RECORDING')
    screenshot('02_recording_consent')
    tap('I understand and have informed');tap('Continue',exact=True)
    for _ in range(8):
        t=tree(); txt=' '.join(n.get('text','') for n in t.iter('node'))
        if prefs().get('recording')=='true':break
        if any(x in txt for x in ['While using the app','Only this time']):maybe('While using the app','Only this time')
        elif 'A single app' in txt:tap('A single app');maybe('Entire screen','Share entire screen')
        elif 'Share one app' in txt:tap('Share one app');maybe('Entire screen','Share entire screen')
        elif not maybe('Start now','Start recording','Share screen','Share entire screen','Entire screen','Allow'):
            time.sleep(.8)
    wait_pref('recording','true')
    check('recording_service_started',True)
    screenshot('03_recording_active')
    before=list_media()
    start_activity(LAB+'/.PlaybackActivity');tap('PLAY TEST SIGNAL',exact=True)
    event('other_app_signal_playing');time.sleep(10);screenshot('04_other_app_recording')
    adb('shell','cmd','statusbar','expand-notifications');time.sleep(1)
    screenshot('05_notification_controls')
    if maybe('Pause'):
        wait_pref('paused','true');check('notification_pause',True);time.sleep(1);maybe('Resume');wait_pref('paused','false');check('notification_resume',True)
    else:
        adb('shell','cmd','statusbar','collapse');start_activity(APP+'/.MainActivity');top();tap('PAUSE / RESUME',exact=True);wait_pref('paused','true');time.sleep(1);tap('PAUSE / RESUME',exact=True);wait_pref('paused','false');check('app_pause_resume',True)
    adb('shell','cmd','statusbar','collapse');start_activity(APP+'/.MainActivity');top();tap('MARK',exact=True)
    check('bookmark_created',bool(prefs().get('bookmarks')))
    screenshot('06_recording_bookmark')
    adb('shell','cmd','statusbar','expand-notifications');time.sleep(.6)
    if not maybe('Stop & save'):
        adb('shell','cmd','statusbar','collapse');start_activity(APP+'/.MainActivity');top();tap('STOP & SAVE',exact=True)
    wait_pref('recording','false',60);adb('shell','cmd','statusbar','collapse');time.sleep(2)
    recorded=pull_new(before,'01_real_capture');d=probe(recorded)
    check('capture_has_video',any(s['codec_type']=='video' for s in d['streams']))
    check('capture_has_audio',any(s['codec_type']=='audio' for s in d['streams']))
    audio=run(['ffmpeg','-hide_banner','-i',str(recorded),'-af','volumedetect','-vn','-f','null','-']).stderr.decode(errors='replace')
    (OUT/'capture-audio-analysis.txt').write_text(audio)
    m=re.search(r'max_volume:\s*([-\d.]+) dB',audio)
    check('digital_playback_audio_non_silent',bool(m) and float(m.group(1))>-60,str(m.group(1) if m else 'not measured'))
    start_activity(APP+'/.MainActivity');screenshot('07_saved_recording')

def single_editor_test():
    event('single_editor_start');start_activity(APP+'/.MainActivity');top();tap('OPEN HAL STUDIO',scroll=True,exact=True)
    screenshot('08_single_editor')
    # Deterministic parser, not an external AI service.
    tap('Example: make a 30 second vertical Short',scroll=True)
    type_text('make a 6 second vertical short, brighter, cinematic, title: HAL CAPTURE')
    adb('shell','input','keyevent','KEYCODE_BACK');tap('PLAN EDIT',scroll=True,exact=True)
    screenshot('09_local_edit_plan');before=list_media();tap('RENDER EDIT',scroll=True,exact=True)
    event('single_render_started');time.sleep(1);screenshot('10_single_render_progress')
    wait_text('Render complete',180);screenshot('11_single_render_saved')
    output=pull_new(before,'02_studio_export');d=probe(output)
    duration=float(d['format']['duration']);check('single_edit_six_seconds',abs(duration-6)<.5,str(duration))
    check('single_edit_has_video',any(s['codec_type']=='video' for s in d['streams']))
    adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)

def timeline_test():
    event('timeline_start');start_activity(APP+'/.MainActivity');top();tap('OPEN TIMELINE STUDIO',scroll=True,exact=True)
    screenshot('12_timeline_empty');tap('ADD LATEST',exact=True);time.sleep(2);tap('ADD LATEST',exact=True);time.sleep(2)
    screenshot('13_timeline_two_clips')
    # Trim first segment to three seconds using real controls.
    tap('TRIM',scroll=True,exact=True);t=tree();fields=[n for n in t.iter('node') if n.get('class')=='android.widget.EditText'];check('trim_dialog_has_two_fields',len(fields)==2)
    edit_field(fields[1],'3');adb('shell','input','keyevent','KEYCODE_BACK');tap('Apply',exact=True)
    tap('IMPORT MUSIC',scroll=True,exact=True)
    # DocumentsUI may open Recent or Downloads; choose the generated local fixture.
    if not maybe('HAL_Test_Music.wav'):
        maybe('Show roots','Open navigation drawer');maybe('Downloads');time.sleep(.8);tap('HAL_Test_Music.wav',scroll=True,exact=True)
    time.sleep(2);screenshot('14_soundtrack_controls')
    tap('YouTube 16:9 / 720p',scroll=True,exact=True);tap('Shorts 9:16 / 720p',exact=True)
    screenshot('15_delivery_preset');before=list_media();tap('EXPORT TIMELINE',scroll=True,exact=True)
    event('timeline_render_started');time.sleep(1);screenshot('16_timeline_render_progress')
    wait_text('Export saved',240);screenshot('17_timeline_export_saved')
    out=pull_new(before,'03_timeline_export');d=probe(out)
    check('timeline_has_audio',any(s['codec_type']=='audio' for s in d['streams']))
    duration=float(d['format']['duration']);check('timeline_trimmed_sequence_duration',8.5<=duration<=9.5,str(duration))
    video=[s for s in d['streams'] if s['codec_type']=='video'][0]
    check('timeline_resolution_720x1280',sorted([video['width'],video['height']])==[720,1280],str([video['width'],video['height']]))
    time.sleep(3);tap('SHARE EXPORT',scroll=True,exact=True);time.sleep(1);screenshot('18_android_share_sheet')
    event('share_sheet_only_no_upload');adb('shell','input','keyevent','KEYCODE_BACK')

if __name__=='__main__':
    video_process=None
    try:
        adb('install','-r','active_projects/HAL_CAPTURE_ANDROID/app/build/outputs/apk/debug/app-debug.apk',timeout=90)
        adb('install','-r','active_projects/HAL_CAPTURE_ANDROID/playbacklab/build/outputs/apk/debug/playbacklab-debug.apk',timeout=90)
        adb('shell','pm','grant',APP,'android.permission.POST_NOTIFICATIONS')
        for command in ['wm size 720x1280','wm density 280','settings put system screen_off_timeout 600000','settings put system show_touches 1','settings put global window_animation_scale 0.5','settings put global transition_animation_scale 0.5','settings put global animator_duration_scale 0.5','input keyevent KEYCODE_WAKEUP','wm dismiss-keyguard']:
            shell(command,check=False)
        run(['ffmpeg','-y','-f','lavfi','-i','sine=frequency=220:sample_rate=48000:duration=3','-filter:a','volume=0.15','HAL_Test_Music.wav'])
        adb('push','HAL_Test_Music.wav','/sdcard/Download/HAL_Test_Music.wav')
        shell('am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Download/HAL_Test_Music.wav',check=False)
        START=time.monotonic();video_process=subprocess.Popen(['adb','shell','screenrecord','--size','720x1280','--bit-rate','3500000','--time-limit','180','/sdcard/hal-emulator-demo.mp4'],stdout=open(OUT/'screenrecord.log','w'),stderr=subprocess.STDOUT)
        for name,fn in [('recorder',recorder_test),('single_editor',single_editor_test),('timeline',timeline_test)]:
            try:fn()
            except Exception as e:
                CHECKS.append({'check':name+'_phase','passed':False,'detail':str(e)});event(name+'_failed:'+str(e));(OUT/(name+'-error.txt')).write_text(traceback.format_exc());screenshot(name+'_failure');adb('shell','input','keyevent','KEYCODE_BACK');adb('shell','cmd','statusbar','collapse',check=False)
    except Exception as e:
        CHECKS.append({'check':'setup','passed':False,'detail':str(e)});(OUT/'setup-error.txt').write_text(traceback.format_exc())
    finally:
        shell('pkill -2 screenrecord',check=False)
        if video_process:
            try:video_process.wait(timeout=15)
            except subprocess.TimeoutExpired:video_process.terminate()
        adb('pull','/sdcard/hal-emulator-demo.mp4',str(OUT/'emulator_walkthrough_raw.mp4'),check=False)
        (OUT/'logcat.txt').write_text(adb('logcat','-d','-v','threadtime',timeout=30,check=False))
        result={'source':'actual Android emulator; production APK, UI automation and separate original test fixture','physical_microphone_tested':False,'published_to_youtube':False,'checks':CHECKS,'events':EVENTS}
        (OUT/'results.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2),flush=True)
    raise SystemExit(1 if any(not c['passed'] for c in CHECKS) else 0)
