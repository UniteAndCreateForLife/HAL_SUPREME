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
p.write_text(s)
p=root/'TimelineActivity.java'
s=p.read_text().replace('private void cancelRender(){if(exporter!=null)', 'private void cancelRender(){main.removeCallbacksAndMessages(null);if(exporter!=null)')
s=s.replace('setOrientation(1)', 'setOrientation(LinearLayout.VERTICAL)').replace('setOrientation(0)', 'setOrientation(LinearLayout.HORIZONTAL)')
assert 'setOrientation(1)' not in s and 'setOrientation(0)' not in s
p.write_text(s)
# An emulator hardware keyboard may hide the IME; Back must not close the editor.
p=Path('active_projects/HAL_CAPTURE_V04_DEMO/demo_test.py')
s=p.read_text()
s=s.replace('def edit_field(node,value):', '''def hide_keyboard():
    state=shell('dumpsys input_method',check=False)
    if any(key in state for key in ('mInputShown=true','mIsInputViewShown=true','isInputViewShown=true')):
        adb('shell','input','keyevent','KEYCODE_BACK')
        time.sleep(.4)
def edit_field(node,value):''')
s=s.replace("adb('shell','input','keyevent','KEYCODE_BACK');tap('PLAN EDIT'", "hide_keyboard();tap('PLAN EDIT'")
s=s.replace("edit_field(fields[1],'3');adb('shell','input','keyevent','KEYCODE_BACK');tap('Apply'", "edit_field(fields[1],'3');hide_keyboard();tap('Apply'")
p.write_text(s)
print('Applied explicit alpha hardening changes')
