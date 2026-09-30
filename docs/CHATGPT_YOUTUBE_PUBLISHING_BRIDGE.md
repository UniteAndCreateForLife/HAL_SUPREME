# ChatGPT → HAL YouTube Publishing Bridge

## Goal

Allow ChatGPT to trigger and verify HAL's existing YouTube upload path without giving the assistant raw OAuth credentials, arbitrary shell access, or implicit publication authority.

The local canonical uploader remains the existing `hal_youtube_uploader.py`. This bridge is an authorization and evidence boundary around it, not a second uploader.

## Required tool surface

### youtube_preflight — read-only

Input:
- optional `publish_id`

Returns:
- uploader present / missing;
- Google client library present / missing;
- OAuth client configuration present / missing;
- refresh-token state: present / missing / invalid (never return token values);
- authenticated YouTube channel identity when available;
- staged publish entry;
- source video path represented by safe logical ID, not a private absolute path;
- source video SHA-256, size, duration, dimensions, codec;
- requested title, description hash, tags, category, audience flag, privacy;
- media/QC gate status;
- duplicate-upload state;
- whether the operation would create an external mutation.

No upload occurs.

### youtube_upload_private — external mutation

Inputs:
- `publish_id`
- `expected_video_sha256`
- `approval_nonce`

Hard rules:
- only a previously staged and QC-eligible item;
- SHA-256 must match the staged receipt;
- default and initial privacy is **private**;
- fail if an existing verified `youtube_video_id` is already recorded for the same release fingerprint;
- use resumable upload;
- never accept arbitrary file paths from the chat caller;
- never return tokens, client secrets, upload-session URLs, or private filesystem paths.

Returns:
- attempt ID;
- YouTube video ID if created;
- observed privacy;
- upload/processing state;
- receipt hash.

### youtube_verify — read-only

Input:
- `video_id` or `publish_id`

Returns:
- YouTube video ID;
- channel ID / safe channel label;
- upload status;
- processing status;
- observed visibility;
- title;
- duration when available;
- local release fingerprint / SHA linkage;
- verified true/false and reason.

### youtube_set_visibility — external mutation

Inputs:
- `video_id`
- `visibility`: private | unlisted | public
- `approval_nonce`

Rules:
- **public** is a distinct approval from upload;
- verify the video belongs to the authorized channel;
- require a verified upload receipt and local release fingerprint;
- read back the new visibility after mutation;
- never infer success from HTTP success alone.

### youtube_upload_status — read-only

Input:
- `attempt_id`

Returns bounded resumable-upload progress and terminal state without leaking the resumable session URI.

## Chat approval model

The assistant may call read-only preflight and verification tools freely.

Before `youtube_upload_private`, show:
- exact title;
- source artifact hash;
- duration / dimensions;
- requested privacy;
- target channel identity;
- whether the file passed HAL media/QC gates.

Require explicit approval for that exact upload.

Before changing to **public**, require a separate explicit approval naming the video/title and public visibility.

## Existing HAL state to preserve

HAL already separates:
1. release preparation/staging;
2. YouTube upload;
3. platform processing/visibility verification.

Keep that separation.

Do not route through any simulated publisher. A successful release requires a real YouTube video ID plus destination/visibility readback.

Duplicate prevention should remain release-fingerprint / artifact-SHA based and should fail closed when a verified YouTube ID is already attached.

## OAuth

Use the narrow YouTube upload scope where practical:

`https://www.googleapis.com/auth/youtube.upload`

Keep refresh credentials only in the local secret store/runtime path. ChatGPT receives only safe auth state and channel identity.

The first authorization is a one-time human Google consent step. After a valid refresh token is stored, routine private uploads can be invoked through the bridge subject to HAL's approval gate.

## Upload implementation

Use YouTube Data API `videos.insert` with resumable upload. Preserve the resumable state only in the trusted local uploader; never return the upload-session URI through MCP.

The bridge should support retry/resume for transient 5xx/network failures and record:
- attempt ID;
- bytes uploaded / total;
- retriable failure class;
- final YouTube video ID;
- source artifact SHA-256;
- metadata revision;
- requested and observed visibility;
- completed receipt SHA-256.

## ChatGPT path

Target flow:

```
ChatGPT
  ↓ youtube_preflight
HAL ChatGPT Bridge
  ↓
canonical publish queue + media/QC receipt
  ↓ explicit user approval
youtube_upload_private
  ↓
hal_youtube_uploader.py
  ↓
YouTube Data API
  ↓
real video ID
  ↓ youtube_verify
ChatGPT receives verified receipt
  ↓ separate approval if desired
youtube_set_visibility(unlisted/public)
```

This lets the video pipeline produce and review media headlessly, while ChatGPT controls only the narrow publish actions the user explicitly authorizes.
