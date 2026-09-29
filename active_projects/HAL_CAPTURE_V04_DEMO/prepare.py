#!/usr/bin/env python3
"""Reconstruct the checksum-verified 0.3 source, then apply explicit 0.4 changes."""
from pathlib import Path
import shutil
import subprocess
import yaml

REPO = Path.cwd()
INPUT = REPO / 'active_projects/HAL_CAPTURE_V04_DEMO'
ROOT = REPO / 'active_projects/HAL_CAPTURE_ANDROID'
workflow = yaml.safe_load((REPO / '.github/workflows/hal-capture-android.yml').read_text())
preparation = {
    'Reconstruct audited source bundle', 'Apply alpha source fixes',
    'Apply HAL Studio 0.3 override', 'Apply Media3 opt-in boundary',
    'Apply Studio regression tests',
}
found = set()
for step in workflow['jobs']['build']['steps']:
    if step.get('name') in preparation:
        subprocess.run(step['run'], shell=True, executable='/bin/bash', check=True)
        found.add(step['name'])
if found != preparation:
    raise RuntimeError('Baseline preparation changed; manual reconciliation required')
java = ROOT / 'app/src/main/java/com/halsupreme/capture'
for name in ('TimelinePlan.java', 'TimelineExporter.java', 'TimelineActivity.java'):
    shutil.copy2(INPUT / name, java / name)
tests = ROOT / 'app/src/test/java/com/halsupreme/capture'
tests.mkdir(parents=True, exist_ok=True)
shutil.copy2(INPUT / 'TimelinePlanTest.java', tests / 'TimelinePlanTest.java')

def replace_exact(path, old, new):
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'Expected one replacement in {path.name}, got {count}: {old[:80]}')
    path.write_text(text.replace(old, new))

p = ROOT / 'app/build.gradle.kts'
replace_exact(p, 'versionCode = 3', 'versionCode = 4')
replace_exact(p, 'versionName = "0.3.0-alpha3"', 'versionName = "0.4.0-alpha4"')
p = ROOT / 'app/src/main/AndroidManifest.xml'
replace_exact(p, 'android:allowBackup="true"', 'android:allowBackup="false"')
replace_exact(p, '<activity\n            android:name=".StudioActivity"', '<activity android:name=".TimelineActivity" android:exported="false" android:configChanges="orientation|screenSize|keyboardHidden" />\n        <activity\n            android:name=".StudioActivity"')
p = java / 'MainActivity.java'
replace_exact(p, '        studio.addView(studioBtn, stp);', '''        studio.addView(studioBtn, stp);
        Button timelineBtn = action("OPEN TIMELINE STUDIO", VIOLET, Color.WHITE);
        timelineBtn.setOnClickListener(v -> startActivity(new Intent(this, TimelineActivity.class)));
        LinearLayout.LayoutParams timelineLayout = fullHeight(48); timelineLayout.topMargin = dp(10);
        studio.addView(timelineBtn, timelineLayout);''')
replace_exact(p, 'HAL Capture • alpha 0.3.0', 'HAL Capture • alpha 0.4.0')
# The dark-themed consent dialog previously used dark-grey body text.
s = p.read_text().replace('setTextColor(Color.DKGRAY)', 'setTextColor(TEXT)')
p.write_text(s)
for name in ('MainActivity.java', 'StudioActivity.java'):
    p = java / name
    replace_exact(p, 'setContentView(buildUi());', '''View page = buildUi();
        page.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(0, insets.getSystemWindowInsetTop(), 0, insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(page);''')
p = java / 'StudioActivity.java'
s = p.read_text()
if 'void onDestroy()' not in s:
    s = s.replace('    private void updateEffectReadout()', '''    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (exporting && exporter != null) exporter.cancel();
        if (preview != null) preview.stopPlayback();
        super.onDestroy();
    }
    private void updateEffectReadout()''')
p.write_text(s)
# Package a separate, permission-free playback fixture for reproducible testing.
lab = ROOT / 'playbacklab'
(lab / 'src/main/java/com/halsupreme/capture/playbackfixture').mkdir(parents=True, exist_ok=True)
shutil.copy2(INPUT / 'PlaybackActivity.java', lab / 'src/main/java/com/halsupreme/capture/playbackfixture/PlaybackActivity.java')
(lab / 'build.gradle.kts').write_text('''plugins { id("com.android.application") }
android {
    namespace = "com.halsupreme.capture.playbackfixture"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.halsupreme.capture.playbackfixture"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "1.0-test-only"
    }
}
''')
(lab / 'src/main/AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<application android:label="HAL Test Signal" android:allowBackup="false" android:allowAudioPlaybackCapture="true" android:theme="@android:style/Theme.Material.NoActionBar">
<activity android:name=".PlaybackActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
</application></manifest>''')
p = ROOT / 'settings.gradle.kts'
p.write_text(p.read_text() + '\ninclude(":playbacklab")\n')
(ROOT / 'RELEASE_0_4.md').write_text('''# HAL Capture Studio 0.4 alpha

Adds a local multi-clip Composition timeline, validated trims, reorder/remove,
local draft restore, optional looping soundtrack, source/music level controls,
audio headroom, 16:9 / 9:16 / 1:1 fit exports, playable MP4 and explicit sharing.
Fixes dark consent-text contrast, app window insets, and single-clip editor lifecycle cleanup.
App backup is disabled. Source media remains unchanged. No network or billing SDK added.

Timeline currently uses hard cuts, not animated transitions. Smart Edit is still a
local deterministic parser in the single-clip editor, not model-generated AI.
Captions, transcription, keyframes and production release remain future work.
Keep the editor screen open while rendering; this is not a resilient background export worker.
Cellular call remote audio is not provided. Source apps may prohibit audio capture.

The playbacklab module is a separate test-only application containing original
animated calibration graphics and generated audio. It is not part of the distributed HAL APK.
Emulator checks do not validate a real microphone, every OEM, or Play Store approval.
''')
print('Prepared HAL Capture 0.4 source at', ROOT)
