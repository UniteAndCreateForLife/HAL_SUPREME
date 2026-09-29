# HAL Capture — Foreground Service Declaration Draft

## mediaProjection

**Functionality**
HAL Capture records the user's screen after the user taps Start Recording and approves Android's MediaProjection consent prompt. Recording can continue while the user opens other apps.

**Why immediate foreground execution is required**
Deferring or interrupting the service would stop or corrupt the screen recording the user explicitly started.

**User visibility and control**
The recording is user-initiated. A persistent notification shows that recording is active and provides pause/resume, bookmark, and stop/save controls. The user can stop recording at any time.

**Play Console use case**
Media or Content Projection and streaming or recording with MediaProjection API.

**Demo video steps**
1. Open HAL Capture.
2. Review and accept the recording advisory.
3. Tap Start Recording.
4. Approve Android's screen-capture prompt.
5. Switch to another app while recording continues.
6. Show the persistent HAL Capture notification.
7. Pause/resume.
8. Stop & Save.
9. Open the saved MP4.

## microphone

**Functionality**
When the user explicitly enables Microphone, HAL Capture records microphone input as part of the user-started recording session.

**Why immediate foreground execution is required**
Interrupting microphone access during the active capture would cause missing audio in the recording.

**User visibility and control**
Microphone recording is optional, permission-gated, initiated from the visible app, and represented by the persistent recording notification. The user can disable the microphone option or stop the recording.

**Demo video steps**
Use the same recording demonstration and visibly enable the Microphone option before starting.
