# Lifelike Performance System

HAL should treat human performance as measured motion first and generated motion second. The highest-fidelity body movement comes from a real performer, synchronized across body, hands, face, gaze, props, audio and ground contacts, then retargeted into the canonical character without destroying root motion or timing.

## Performance stack

1. **Body capture**
   - Preferred production sources: optical marker capture, high-quality multi-camera markerless capture, or calibrated inertial full-body capture.
   - Preserve world-space root position, root orientation, joint rotations, velocities, accelerations and original timecode.
   - Capture at high temporal resolution, then resample only after solving; never infer a low-rate body track from the final rendered video when the source performance exists.

2. **Hands**
   - Fingers require their own capture channel. Do not derive final finger performance from wrist pose alone.
   - Store per-finger joint rotations plus grasp/contact events and the object/contact frame.

3. **Face, eyes and voice**
   - Capture facial performance and audio from the same take whenever possible.
   - Preserve head motion, eye/gaze targets, eyelids, brows, cheeks, jaw, lips, tongue/teeth visibility where available, and phoneme timing.
   - Audio-only facial generation is a fallback, not a replacement for an available facial performance.

4. **Prop and environment contact**
   - A hand touching a prop, a foot touching the floor, or a body leaning on a wall becomes a persistent contact constraint.
   - Contact constraints outrank cosmetic animation blending: no foot skating, hand sliding, ground penetration, or independently drifting props.
   - Tracked props should keep their measured transform/inertia whenever capture data exists.

5. **Canonical retarget**
   - Retarget solved motion onto the canonical HAL humanoid skeleton using an explicit bone map and body-proportion calibration.
   - Preserve root motion. Apply IK as a corrective layer for contact and proportion differences, not as the primary source of human movement.
   - Record the capture skeleton, retarget profile, scale correction and resulting motion artifact as provenance.

6. **Continuous-life controller**
   - Characters never enter a perfectly frozen idle.
   - A slower cognitive/life-state layer chooses gaze target, posture, intent, gesture tendency and breathing state.
   - A 30-60+ Hz motor layer blends captured locomotion/performance, root trajectory, contact corrections, micro-posture, breathing, blinking, saccades, finger settling and secondary motion.
   - Shot cuts do not reset the body. Root transform, root velocity, angular velocity, foot contacts, hand contacts, gaze target, breath phase, current gesture/animation phase and carried-prop transforms transfer across the cut unless the story declares a discontinuity.

7. **Motion library and motion matching**
   - Build a reusable database from accepted real performances: starts, stops, turns, walks, runs, crouches, reaches, sits, rises, leans, looks, gestures, object interactions and emotional variants.
   - Motion matching may select the closest captured pose/trajectory continuously so synthetic agents move through real human motion instead of switching between canned clips.
   - Generative motion may propose missing transitions or novel actions, but production acceptance still requires contact, joint-limit, continuity and visual-motion QC.

8. **Deformation and secondary physics**
   - Skeleton motion alone is insufficient for photorealism.
   - Drive corrective blendshapes for shoulders, elbows, wrists, hips, knees, neck and facial/body volume from joint pose.
   - Run cloth, coat tails, hair, jewelry and soft secondary motion from the same world-space motion and collision stage.
   - These simulations must be checkpointable so a shot can resume without changing physical state arbitrarily.

## Capture tiers

### Maximum-fidelity studio
Use a calibrated optical or high-end markerless multi-camera stage, synchronized prop tracking, dedicated hand/finger capture and a facial HMC/depth capture system. This is the reference-quality path for hero performances.

### Strong practical HAL stage
Use a calibrated 4-8 camera markerless body volume, dedicated finger gloves or optical hands, a dedicated face camera/phone, synchronized audio and tracked hero props. This should be the main attainable target for HAL.

### Open/local research path
Use FreeMoCap or another calibrated multi-camera solver to produce world-space skeleton data, then run our own cleanup, contact solve, retarget and QC. Single-camera video is useful as a fallback or reference solve but should not replace multi-view capture for difficult occlusion, contact and depth-sensitive hero acting.

## Godot runtime

The canonical character runs inside the same persistent Godot world as the reconstructed environment.

Recommended evaluation order:
1. import and validate the canonical skeleton;
2. retarget one clean captured performance;
3. apply root motion through the character controller;
4. add foot/hand contact solvers using current world geometry;
5. add gaze/head/eye control;
6. add facial curves and finger motion;
7. add continuous-life micro-motion;
8. add cloth/hair/secondary physics;
9. build a captured-motion database and motion matching;
10. only then apply neural video/photoreal finishing.

Godot's native animation tree and root-motion path remain the stable base. Any community motion-matching extension is experimental until HAL's own tests prove skeleton compatibility, determinism and resume integrity.

## Performance QC

A hero take must fail closed on:
- persistent foot skating during declared stance;
- hand/object contact slip beyond tolerance;
- visible ground/body penetration;
- discontinuous pelvis/root velocity without a declared impact/cut;
- impossible joint limits or bone-length changes;
- frame-to-frame pose jitter;
- character teleportation or motion-vector discontinuity;
- lost prop attachment;
- pose/identity drift introduced by the neural finishing pass;
- facial timing that visibly disagrees with the source take;
- frozen-body intervals during a state that should contain natural micro-motion.

Useful measured outputs include foot-contact error, hand-contact error, root jerk, joint angular-velocity outliers, bone-length variance, ground penetration, prop-relative transform error and pose reprojection error against the source cameras.

## First HAL proof

Do not begin with a long film. Capture one 10-20 second performance containing:

walk in -> stop -> weight shift -> look toward the window -> breathe -> reach toward a prop -> release -> turn -> walk out.

Capture body, hands and face from one synchronized performance. Retarget it to the canonical character in the persistent corridor and render it from at least two cameras without resetting the body state between cuts.

The proof passes only if:
- feet stay planted when planted;
- weight transfer reads naturally;
- fingers and prop contacts agree;
- the face/head/gaze agree with the performance;
- clothing and hair react continuously;
- the second camera sees exactly the same continuing body state;
- a post-render continuity audit confirms the neural finishing pass did not change the pose or identity.

Once that passes, HAL has a reusable performance-capture and continuous-life substrate rather than another collection of isolated animation clips.
