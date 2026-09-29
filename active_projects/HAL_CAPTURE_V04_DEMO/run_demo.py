#!/usr/bin/env python3
import demo_test as t
import subprocess, time, json, traceback
from pathlib import Path

process=None
try:
    t.adb('install','-r','active_projects/HAL_CAPTURE_ANDROID/app/build/outputs/apk/debug/app-debug.apk',timeout=90)
    t.adb('install','-r','active_projects/HAL_CAPTURE_ANDROID/playbacklab/build/outputs/apk/debug/playbacklab-debug.apk',timeout=90)
    t.adb('shell','pm','grant',t.APP,'android.permission.POST_NOTIFICATIONS')
    for cmd in ['wm size 720x1280','wm density 280','settings put system screen_off_timeout 600000','settings put system show_touches 1','settings put global window_animation_scale 0.5','settings put global transition_animation_scale 0.5','settings put global animator_duration_scale 0.5','input keyevent KEYCODE_WAKEUP','wm dismiss-keyguard']:
        t.shell(cmd,check=False)
    t.run(['ffmpeg','-y','-f','lavfi','-i','sine=frequency=220:sample_rate=48000:duration=3','-filter:a','volume=0.15','HAL_Test_Music.wav'])
    t.adb('push','HAL_Test_Music.wav','/sdcard/Download/HAL_Test_Music.wav')
    t.shell('am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Download/HAL_Test_Music.wav',check=False)
    t.START=time.monotonic()
    for name,fn in [('recorder',t.recorder_test),('single_editor',t.single_editor_test),('timeline',t.timeline_test)]:
        remote='/sdcard/hal_'+name+'_walkthrough.mp4'
        t.event('phase_video_start:'+name)
        with open(t.OUT/(name+'-screenrecord.log'),'w') as log:
            process=subprocess.Popen(['adb','shell','screenrecord','--size','720x1280','--bit-rate','3500000','--time-limit','180',remote],stdout=log,stderr=subprocess.STDOUT)
            try:
                time.sleep(.5);fn()
            except Exception as error:
                t.CHECKS.append({'check':name+'_phase','passed':False,'detail':str(error)})
                t.event(name+'_failed:'+str(error))
                (t.OUT/(name+'-error.txt')).write_text(traceback.format_exc())
                t.screenshot(name+'_failure')
                t.adb('shell','input','keyevent','KEYCODE_BACK')
                t.adb('shell','cmd','statusbar','collapse',check=False)
            finally:
                t.shell('pkill -2 screenrecord',check=False)
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:process.terminate()
                t.adb('pull',remote,str(t.OUT/(name+'_walkthrough.mp4')),check=False)
                t.event('phase_video_end:'+name)
                process=None
except Exception as error:
    t.CHECKS.append({'check':'setup','passed':False,'detail':str(error)})
    (t.OUT/'setup-error.txt').write_text(traceback.format_exc())
finally:
    if process:
        t.shell('pkill -2 screenrecord',check=False);process.terminate()
    (t.OUT/'logcat.txt').write_text(t.adb('logcat','-d','-v','threadtime',timeout=30,check=False))
    result={'source':'Actual Android emulator, UI-driven production app and separate original test fixture','physical_microphone_tested':False,'published_to_youtube':False,'checks':t.CHECKS,'events':t.EVENTS}
    (t.OUT/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
raise SystemExit(1 if any(not c['passed'] for c in t.CHECKS) else 0)
