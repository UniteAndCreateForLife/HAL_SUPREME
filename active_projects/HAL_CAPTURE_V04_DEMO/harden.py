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
p.write_text(s)
print('Applied explicit alpha hardening changes')
