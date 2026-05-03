# DSP Form Lab

**DSP Form Lab** is a starter repo for turning audio, DSP traces, MIDI/OSC/control data, and seeded procedural systems into 3D forms: OBJ for studio exchange, STL/3MF for fabrication, PNG previews for quick review, and JSON manifests for repeatability.

This is meant to behave less like a single “audio visualizer” and more like a small sculptural instrument:

```text
WAV / seed / MIDI / OSC / CSV
        ↓
feature extraction
        ↓
geometry grammar
        ↓
mesh export + repair
        ↓
OBJ / STL / preview / manifest
```

The repo starts with four practical direct-mesh grammars and one grammar-score lane:

1. **Spectrogram terrain** — time × frequency becomes a printable relief tile.
2. **Waveform ribbon** — amplitude/envelope becomes a swept 3D ribbon.
3. **Circular vessel** — time wraps around a circle; features become radius, height, ridges, or texture.
4. **Helical body** — time climbs a spiral; features become coil radius, tube thickness, and torsion.
5. **StructureSynth grammar body** — a captured WAV becomes an EisenScript grammar score for recursive growth.

A sixth path, **implicit field**, is included as a future direction for marching-cubes / scalar-field forms.

## Why this repo exists

This project sits at the intersection of:

- DSP experiments and sound instruments.
- Seeded/generative audio systems.
- Tactile control surfaces such as MIDI/OSC knob boxes.
- Mesh generation and fabrication pipelines.
- Classroom-safe creative coding.
- Reproducible studio practice.

The guiding principle is simple:

> Every object should know how it was born.

Each generated mesh should have a nearby manifest recording the source file, seed, parameters, generator version, dimensions, output paths, and warnings.
Manifests also record seed usage mode (`geometry_rng`, `grammar_rng`, or `metadata_only`) so seed behavior is explicit per lane.

## Current status

The repo has now completed a first local multi-form pass from a real WAV:

- terrain run completed
- vessel run completed
- helix run completed
- feature CSV + manifest export confirmed
- helix parameter sweep confirmed

What is still not proven:

- Blender review
- slicer review
- first print
- photo/notes from physical results

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Generate a test audio file:

```bash
dspform sample --out audio/samples/sine_sweep.wav
```

Generate a terrain tile:

```bash
dspform terrain audio/samples/sine_sweep.wav --out outputs/obj/sine_sweep_terrain.obj
# optional seeded texture variation:
#   --texture-noise-mm 0.6 --seed 42
```

Generate a ribbon:

```bash
dspform ribbon audio/samples/sine_sweep.wav \
  --out outputs/obj/sine_sweep_ribbon.obj \
  --wobble-mm 0.0
```

Generate a vessel:

```bash
dspform vessel audio/samples/sine_sweep.wav --out outputs/obj/sine_sweep_vessel.obj
# optional seeded variation:
#   --angle-jitter-deg 6 --radius-noise-mm 0.8 --seed 42
```

Generate a helix:

```bash
dspform helix audio/samples/sine_sweep.wav --out outputs/obj/sine_sweep_helix.obj
# optional seeded variation:
#   --turns 4.5 --tube-radius 4.8 --angle-jitter-deg 4 --radius-noise-mm 0.8 --seed 42
```

Generate a StructureSynth / EisenScript grammar score:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --csv data/features/sine_sweep_features.csv \
  --template onset-lattice \
  --seed 42 \
  --max-events 24
```

Or generate the spiral-growth variant:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_helix_coil.es \
  --template helix-coil \
  --seed 42 \
  --max-events 24
```

Or generate a tighter threaded spiral variant:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_helix_thread.es \
  --template helix-thread \
  --seed 42 \
  --max-events 24
```

Or generate a more continuous vine-like spiral variant:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_helix_vine.es \
  --template helix-vine \
  --seed 42 \
  --max-events 24
```

The mesh commands write:

- `.obj` mesh file
- `.json` manifest
- optional `.csv` feature dump

The `ssynth` command writes:

- `.es` EisenScript grammar
- `.json` manifest
- optional `.csv` feature dump

Generate a seeded family (batch seed sweep):

```bash
dspform seed-sweep audio/samples/sine_sweep.wav \
  --generator terrain \
  --out-dir outputs/obj/seed_sweeps \
  --seed-start 0 \
  --seed-count 8 \
  --seed-step 1 \
  --texture-noise-mm 0.6
```

This writes one output per seed plus an index manifest:

- `*_seed_sweep.json` (seed list + per-seed output/manifest paths)

Generate a parameter sweep with comparison CSV:

```bash
dspform param-sweep audio/samples/sine_sweep.wav \
  --generator vessel \
  --param radius_noise_mm \
  --values 0.0,0.4,0.8,1.2 \
  --seed 42 \
  --out-dir outputs/obj/param_sweeps
```

This writes one output per value plus:

- `*_comparison.csv` (per-run manifest + mesh metrics)
- `*_param_sweep.json` (sweep index and artifact paths)

Render a contact sheet from any sweep index:

```bash
dspform contact-sheet outputs/obj/param_sweeps/sine_sweep_vessel_radius_noise_mm_param_sweep.json \
  --out outputs/previews/sine_sweep_vessel_radius_noise_sheet.png
```

Open the `.es` file in StructureSynth or BrowserSynth, export OBJ, then inspect the OBJ through the same Blender/MeshLab/slicer path as the Python-generated meshes.

## Practical first milestone

The first real milestone is not a perfect sculpture. It is this:

```text
one WAV in → one valid OBJ out → one manifest beside it → one print-safe checklist pass
```

That tiny pipeline is the seed crystal for the whole system.

The repo is now slightly past the first half of that milestone:

```text
one WAV in → multiple valid OBJ bodies out → manifests beside them
```

The remaining proof is physical and visual, not just computational.

## Repo map

```text
src/dspform/             Python package
src/dspform/generators/  geometry grammars
src/dspform/mesh/        mesh export / inspection / repair helpers
docs/                    concept, workflow, equipment, references
sketches/processing/     Processing examples and live-teaching sketches
blender/scripts/         Blender preview/render helpers
pipelines/structuresynth/ StructureSynth / EisenScript grammar-score lane
examples/                small project recipes
audio/                   local samples and generated audio
data/                    features, fields, manifests
outputs/                 generated meshes and previews
```

## Suggested next links to your existing practice

- Use **SeedBox** or other seeded DSP instruments to render repeatable WAVs.
- Use **MOARkNOBS-42** as a controller for parameters such as height, smoothing, twist, decimation, ridge depth, and seed selection.
- Use frZone-style band triggers to place mesh events such as ribs, spikes, cuts, openings, or root structures.
- Use StructureSynth when the sound should become a recursive grammar/body rather than a direct waveform surface.
- Use Blender and MeshLab for visual inspection before sending anything to a printer.

## License

MIT. See `LICENSE`.
