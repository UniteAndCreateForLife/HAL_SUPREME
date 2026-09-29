#!/usr/bin/env python3
from pathlib import Path
root=Path('active_projects/HAL_CAPTURE_ANDROID/app/src/main/java/com/halsupreme/capture')
p=root/'MainActivity.java'
s=p.read_text().replace(', 14, Color.DKGRAY, false)', ', 14, TEXT, false)')
s=s.replace('1080p target • screen + optional microphone','Screen + supported device audio + optional microphone')
p.write_text(s)
p=root/'StudioActivity.java'
s=p.read_text().replace('HAL STUDIO 0.3','HAL STUDIO 0.4')
s=s.replace('Next layers: multi-clip Composition timeline, background music, captions/transcription, keyframes, transitions, LUTs, voice cleanup, highlight detection and model-backed edit planning.', 'Multi-clip timelines and music are available from the Capture screen. Next layers: captions/transcription, keyframes, transitions, LUTs, voice cleanup, highlight detection and model-backed edit planning.')
s=s.replace('LinearLayout root = col();','LinearLayout root = col();\n        root.setFocusableInTouchMode(true); root.requestFocus();')
s=s.replace('preview = new VideoView(this);','preview = new VideoView(this);\n        preview.setFocusable(false); preview.setFocusableInTouchMode(false);')
p.write_text(s)
p=root/'TimelineActivity.java'
s=p.read_text().replace('private void cancelRender(){if(exporter!=null)', 'private void cancelRender(){main.removeCallbacksAndMessages(null);if(exporter!=null)')
s=s.replace('setOrientation(1)', 'setOrientation(LinearLayout.VERTICAL)').replace('setOrientation(0)', 'setOrientation(LinearLayout.HORIZONTAL)')
s=s.replace('LinearLayout root = column(); root.setPadding', 'LinearLayout root = column(); root.setFocusableInTouchMode(true); root.requestFocus(); root.setPadding')
s=s.replace('preview=new VideoView(this);', 'preview=new VideoView(this);preview.setFocusable(false);preview.setFocusableInTouchMode(false);')
s=s.replace('restoreDraft();refresh();', 'restoreDraft();refresh();root.requestFocus();scroll.post(()->scroll.scrollTo(0,0));')
assert 'setOrientation(1)' not in s and 'setOrientation(0)' not in s
p.write_text(s)
# Keep the actual Android 12+ splash screen consistent with the app's dark theme.
res=root.parents[5]/'res'
# Use the explicit path rather than depending on the source package depth.
res=Path('active_projects/HAL_CAPTURE_ANDROID/app/src/main/res')
v31=res/'values-v31';v31.mkdir(exist_ok=True)
style=(res/'values/styles.xml').read_text()
style=style.replace('</style>', '<item name="android:windowSplashScreenBackground">#090A0F</item>\n        <item name="android:windowSplashScreenAnimatedIcon">@drawable/ic_hal</item>\n    </style>')
(v31/'styles.xml').write_text(style)
# Match exact system approval labels; never confuse the explanatory title with a button.
p=Path('active_projects/HAL_CAPTURE_V04_DEMO/demo_test.py')
s=p.read_text()
s=s.replace("adb('shell','am','start','-n',component);time.sleep(1.2)", "adb('shell','am','start','-W','-n',component);time.sleep(2.0)")
s=s.replace("if any(x in txt for x in ['While using the app','Only this time']):", "if any(n.get('text')=='Start' for n in t.iter('node')):\n            screenshot('02b_android_screen_consent');tap('Start',exact=True)\n        elif any(x in txt for x in ['While using the app','Only this time']):")
s=s.replace("'Start now','Start recording','Share screen'", "'Start now','Share screen'")
s=s.replace('def edit_field(node,value):', '''def hide_keyboard():
    state=shell('dumpsys input_method',check=False)
    if any(key in state for key in ('mInputShown=true','mIsInputViewShown=true','isInputViewShown=true')):
        adb('shell','input','keyevent','KEYCODE_BACK')
        time.sleep(.4)
def edit_field(node,value):''')
s=s.replace("adb('shell','input','keyevent','KEYCODE_BACK');tap('PLAN EDIT'", "hide_keyboard();tap('PLAN EDIT'")
s=s.replace("edit_field(fields[1],'3');adb('shell','input','keyevent','KEYCODE_BACK');tap('Apply'", "edit_field(fields[1],'3');hide_keyboard();tap('Apply'")
s=s.replace("screenshot('12_timeline_empty');tap('ADD LATEST'", "top();screenshot('12_timeline_empty');tap('ADD LATEST'")
s=s.replace("event('single_editor_start');start_activity", "check('capture_available_for_single_editor',bool(prefs().get('latest_uri')));event('single_editor_start');start_activity")
p.write_text(s)
print('Applied explicit alpha hardening changes')
