# HAL Light Cathedral native Godot render proof

This isolated experiment exists only to produce a native Godot render from the real 3D cathedral asset.

- Godot: 4.7.2 stable
- Asset: cathedral_full_environment_v11.glb
- Geometry is real GLB 3D mesh data.
- main.gd animates the camera, prisms, lenses, suspended orbs, performer proxy, and real Godot lights.
- No concept-art image is used as scenery.

The GitHub Actions workflow renders a 5-second canary using Godot Movie Maker under Xvfb/Mesa and uploads the MP4 plus the Godot log.
