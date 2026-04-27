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

The repo starts with three practical direct-mesh grammars and one grammar-score lane:

1. **Spectrogram terrain** — time × frequency becomes a printable relief tile.
2. **Waveform ribbon** — amplitude/envelope becomes a swept 3D ribbon.
3. **Circular vessel** — time wraps around a circle; features become radius, height, ridges, or texture.
4. **StructureSynth grammar body** — a captured WAV becomes an EisenScript grammar score for recursive growth.

A fifth path, **implicit field**, is included as a future direction for marching-cubes / scalar-field forms.

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
```

Generate a ribbon:

```bash
dspform ribbon audio/samples/sine_sweep.wav --out outputs/obj/sine_sweep_ribbon.obj
```

Generate a vessel:

```bash
dspform vessel audio/samples/sine_sweep.wav --out outputs/obj/sine_sweep_vessel.obj
```

Generate a StructureSynth / EisenScript grammar score:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --csv data/features/sine_sweep_features.csv \
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

Open the `.es` file in StructureSynth or BrowserSynth, export OBJ, then inspect the OBJ through the same Blender/MeshLab/slicer path as the Python-generated meshes.

## Practical first milestone

The first real milestone is not a perfect sculpture. It is this:

```text
one WAV in → one valid OBJ out → one manifest beside it → one print-safe checklist pass
```

That tiny pipeline is the seed crystal for the whole system.

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
