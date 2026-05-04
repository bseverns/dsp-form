# Dynamic Forms

This lane moves DSP Form Lab from "audio becomes shape" toward "audio becomes
behavior, and the object is the fossil of that behavior."

The older direct mappings are still useful. A terrain tile can say "this bright
frame is high" or "this onset makes a ridge." Dynamic forms add a middle layer:
the audio acts on a small body over time. The final mesh is not just a graph of
features. It is the accumulated trace of pushes, pulls, wounds, growth, cooling,
and repair.

## Audio as behavior

In this model, features are verbs:

- Loudness pushes. It builds growth pressure and gives the body momentum.
- Brightness pulls. It biases the centerline upward, sideways, or toward an axis.
- Onsets wound. They leave scars, ribs, knots, cuts, branch starts, or faultlines.
- Silence heals. It smooths, thins, cools, or lets damage fade.
- Roughness twists. It rotates frames, braids surface lobes, or disturbs growth.
- Repetition grows structure. A single transient can be a nick; repeated events can become a rib field, organ, braid, or branching habit.

This should stay practical. The point is not to build a huge physics engine.
The first useful version is a small stateful grammar that turns frame-level
features into form decisions.

## State and memory

Dynamic forms need memory because sculptural behavior depends on what happened
before.

Useful first-pass state:

- `energy_memory`: loudness with attack/release behavior.
- `damage_memory`: accumulated onset/event damage that can heal during silence.
- `growth_pressure`: slow pressure that affects centerline step size and radius.
- `cooldown`: an event afterimage so clustered hits behave differently from isolated hits.
- `brightness_memory` and `roughness_memory`: smoothed pull/twist signals.

The memory value should be exposed as a studio parameter. Low memory produces
more reactive forms. High memory produces relics: slow changes, persistent
scars, and stronger evidence of history.

## Gestures instead of only frames

Frame-by-frame mapping is a good raw material, but it is too literal on its own.
A dynamic grammar should extract gestures/events first:

- `pulse`: one compact hit.
- `burst`: a short active region.
- `cluster`: repeated or sustained attacks close together.
- `silence`: a quiet region long enough to matter.

These gestures do not replace the continuous features. They sit beside them.
Continuous features drive pressure, pull, twist, and thickness. Gestures decide
where behavior changes: scar here, branch here, heal here, tighten here.

## Style profiles

Profiles should be understandable sculptural intentions, not hidden presets.
They can share the same feature layer and state helpers while emphasizing
different behaviors.

- `scar`: onsets cut or bruise the surface; silence only partly heals.
- `bloom`: events swell outward and can grow small branches or buds.
- `braid`: roughness and repetition twist the body into lobed, woven surfaces.
- `faultline`: events create directional splits, sharp grooves, and lateral drift.
- `organ`: smoother growth, softer scarring, thicker biological tube language.
- `relic`: high memory, slow pressure, persistent damage, weathered surfaces.

These are starting points for form families. They should remain editable,
parameterized, and manifest-recorded.

## Animation-first, fossilized-motion later

A future dynamic-form lane can be animation-first:

1. Simulate a centerline, skin, or branching organism through time.
2. Preview the behavior as motion.
3. Choose one or more moments to freeze.
4. Export the frozen mesh as the fossil of the behavior.

The current implementation can skip real-time animation and still follow the
same concept. It integrates behavior over frames and exports the resulting
object. Later, the same state updates could drive Blender animation, viewport
previews, or frame-by-frame mesh snapshots.

## Difference from ordinary audio visualization

Ordinary visualization usually asks: "What does the audio look like right now?"

Dynamic form generation asks: "What did the audio do to this object over time?"

That difference changes the design:

- Feature values are forces and events, not just coordinates.
- Repetition matters because memory accumulates.
- Silence is active because it can heal, cool, or erase.
- The mesh records history, not only instantaneous amplitude or spectrum.
- A manifest must record not just the source audio, but the behavior parameters,
  seed usage, gesture extraction settings, and mesh-health report.

The goal is a studio-facing sculptural grammar: reproducible enough to rerun,
simple enough to teach, and open-ended enough to keep producing surprising
objects.
