# Media preflight

HAL's render pipeline already rejects still-frame video through `qc.motion`.
This preflight adds structural evidence before a render is treated as
reviewable or promoted into a longer production pass.

It checks:

- a decodable video stream is present;
- minimum duration;
- minimum resolution;
- minimum frame rate;
- audio presence when the production requires it;
- HAL's existing temporal-motion gate.

The structural probe uses `ffprobe` JSON. The motion gate continues to use the
existing sampled-frame hash check in `qc.motion`.

The module fails closed. A missing file, failed probe, malformed probe,
structural policy failure, or missing motion evidence raises
`MediaPreflightError`.

Example:

```python
from pathlib import Path
from qc.media_preflight import require_media_preflight

receipt = require_media_preflight(
    Path("candidate.mp4"),
    min_width=1280,
    min_height=720,
    min_fps=23.0,
    require_audio=True,
)
```

Run the focused tests:

```bash
python -m unittest -v tests.test_media_preflight
```

This is a reusable quality gate, not a release authority. Project-specific
picture, loudness, story, identity, lip-sync, and human review gates remain
separate.
