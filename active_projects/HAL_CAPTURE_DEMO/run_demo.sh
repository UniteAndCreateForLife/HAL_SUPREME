#!/usr/bin/env bash
set -euo pipefail

PKG="com.halsupreme.capture"
MAIN="$PKG/.MainActivity"
OUT_DIR="$GITHUB_WORKSPACE/active_projects/HAL_CAPTURE_DEMO/output"
mkdir -p "$OUT_DIR/ui" "$OUT_DIR/frames"

dump_ui() {
  local name="${1:-ui}"
  adb shell uiautomator dump /sdcard/window.xml >/dev/null 2>&1 || true
  adb exec-out cat /sdcard/window.xml > "$OUT_DIR/ui/${name}.xml" 2>/dev/null || true
}

shot() {
  local name="$1"
  adb exec-out screencap -p > "$OUT_DIR/frames/${name}.png"
}

find_center() {
  local needle="$1"
  dump_ui current
  python3 - "$needle" "$OUT_DIR/ui/current.xml" <<'PY'
import re,sys,xml.etree.ElementTree as ET
needle=sys.argv[1].lower()
path=sys.argv[2]
try: root=ET.parse(path).getroot()
except Exception: sys.exit(1)
for n in root.iter("node"):
    hay=" ".join([n.attrib.get("text",""),n.attrib.get("content-desc",""),n.attrib.get("hint","")]).lower()
    if needle in hay:
        m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.attrib.get("bounds",""))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            print((x1+x2)//2,(y1+y2)//2)
            sys.exit(0)
sys.exit(1)
PY
}

tap_contains() {
  local needle="$1"
  local xy
  xy="$(find_center "$needle" 2>/dev/null || true)"
  if [[ -n "$xy" ]]; then
    adb shell input tap $xy
    sleep 0.8
    return 0
  fi
  return 1
}

wait_tap() {
  local needle="$1"
  for _ in $(seq 1 20); do
    if tap_contains "$needle"; then return 0; fi
    sleep 0.7
  done
  echo "Could not find UI text: $needle" >&2
  dump_ui "missing-${needle//[^A-Za-z0-9]/_}"
  return 1
}

wait_text() {
  local needle="$1"
  for _ in $(seq 1 30); do
    if find_center "$needle" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  echo "Timed out waiting for: $needle" >&2
  return 1
}

scroll_down() { adb shell input swipe 540 1900 540 650 450; sleep 1; }

echo "Installing final HAL Capture build"
adb install -r "$GITHUB_WORKSPACE/active_projects/HAL_CAPTURE_ANDROID/app/build/outputs/apk/debug/app-debug.apk"
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS || true
adb shell pm grant "$PKG" android.permission.RECORD_AUDIO || true

adb shell am force-stop "$PKG"
adb shell am start -n "$MAIN"
sleep 3
shot "01-home"

# External proof recording. The app will simultaneously create its own internal recording.
adb shell rm -f /sdcard/hal_capture_real_use.mp4
adb shell screenrecord --bit-rate 8000000 --time-limit 170 /sdcard/hal_capture_real_use.mp4 >/tmp/hal-screenrecord.log 2>&1 &
SCREEN_PID=$!
sleep 2

wait_tap "START RECORDING"
wait_tap "I understand and have informed participants"
wait_tap "Continue"
sleep 1
dump_ui "projection-prompt"

# Android versions label the MediaProjection prompt differently.
tap_contains "Entire screen" || true
sleep 0.5
if ! tap_contains "Share"; then
  tap_contains "Start now" || tap_contains "Start recording" || tap_contains "Allow" || true
fi
sleep 4
shot "02-recording"

# Prove the recorder keeps working while another app is foreground.
adb shell am start -a android.settings.SETTINGS >/dev/null
sleep 4
shot "03-settings-recorded"
adb shell input swipe 540 1800 540 800 500
sleep 2
adb shell input swipe 540 1800 540 900 500
sleep 2

adb shell am start -n "$MAIN" >/dev/null
sleep 3
shot "04-back-to-hal"
wait_tap "STOP & SAVE"
sleep 6
shot "05-saved"

# Enter real Studio.
for _ in $(seq 1 5); do
  if tap_contains "OPEN HAL STUDIO"; then break; fi
  scroll_down
done
wait_text "HAL STUDIO 0.3"
sleep 2
shot "06-studio"

# Preview the actual captured file.
tap_contains "PLAY / PAUSE" || true
sleep 3
tap_contains "PLAY / PAUSE" || true

# Navigate to HAL Smart Edit and apply a real local edit plan.
for _ in $(seq 1 5); do
  if find_center "PLAN EDIT" >/dev/null 2>&1; then break; fi
  scroll_down
done
dump_ui "studio-smart-edit"
# Tap the lowest visible EditText (Smart Edit prompt field on this screen region).
python3 - "$OUT_DIR/ui/studio-smart-edit.xml" <<'PY' > /tmp/edit_xy
import re,sys,xml.etree.ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
items=[]
for n in root.iter("node"):
    if n.attrib.get("class")=="android.widget.EditText":
        m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.attrib.get("bounds",""))
        if m:
            x1,y1,x2,y2=map(int,m.groups()); items.append(((y1+y2)//2,(x1+x2)//2))
if not items: sys.exit(1)
y,x=max(items)
print(x,y)
PY
if [[ -s /tmp/edit_xy ]]; then
  adb shell input tap $(cat /tmp/edit_xy)
  adb shell input text "make%sa%svertical%sshort%sbrighter%scinematic"
  sleep 1
  wait_tap "PLAN EDIT"
  sleep 2
  # Dismiss the software keyboard so the lower export controls can scroll into view.
  adb shell input keyevent 4 || true
  sleep 1
fi
shot "07-smart-plan"

# Render the planned edit. This proof must fail if an edited file is not actually produced.
for _ in $(seq 1 8); do
  if find_center "RENDER EDIT" >/dev/null 2>&1; then break; fi
  scroll_down
done
wait_tap "RENDER EDIT"
sleep 2
shot "08-rendering"
wait_text "Render complete"
sleep 2
shot "09-render-complete"

# Open the Android share flow as proof of publish handoff, then back out.
tap_contains "SHARE LATEST TO YOUTUBE" || true
sleep 3
shot "10-share-sheet"
adb shell input keyevent 4 || true
sleep 1

# Finish the external proof recording.
adb shell killall -2 screenrecord >/dev/null 2>&1 || true
wait "$SCREEN_PID" || true
sleep 2
adb pull /sdcard/hal_capture_real_use.mp4 "$OUT_DIR/hal_capture_real_use.mp4"

# Capture app state and media inventory as proof receipts.
adb shell dumpsys package "$PKG" > "$OUT_DIR/package.txt"
adb shell content query --uri content://media/external/video/media --projection _id:_display_name:relative_path:duration > "$OUT_DIR/media_inventory.txt"
grep -q "Movies/HAL Capture/Edits" "$OUT_DIR/media_inventory.txt"
grep -q "HAL_Studio_" "$OUT_DIR/media_inventory.txt"
ls -lh "$OUT_DIR/hal_capture_real_use.mp4"
