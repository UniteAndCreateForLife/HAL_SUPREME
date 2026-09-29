# HAL Capture — Google Play Data Safety Draft

Scope: HAL Capture 0.2.0-alpha2 only. Re-evaluate this form whenever analytics, cloud AI, direct upload APIs, ads, billing SDKs, accounts, or other network SDKs are added.

## Current implementation
The current build performs screen/audio capture and media editing on-device. It contains no analytics SDK, ad SDK, account system, or automatic cloud upload.

## Suggested Play Console answers for this build
- Does the app collect or share any required user data types? **No**, based on the present code, because screen/audio content and recordings are processed locally and are not transmitted to the developer.
- User-initiated Android sharing is initiated explicitly by the user through the system share flow. Re-evaluate this answer if HAL Capture itself begins uploading media to a server or direct platform API.
- Data encrypted in transit: not applicable to developer collection in the current build.
- Account deletion: not applicable; the current build has no HAL Capture account.
- Users control local recordings through Android storage/media controls and HAL Capture's local workflow.

## Sensitive access that must still be disclosed in the privacy policy
- Screen content selected through Android MediaProjection
- Microphone audio when enabled
- Supported media/game playback audio when enabled and permitted by Android/source app
- Local recordings, trims, bookmarks, and app preferences

## Release gate
Before submission, verify the final APK/AAB contains no added SDK or network path that changes these answers.
