# StructureSynth Pipeline

This lane treats a captured WAV as a **grammar score**.

The Python mesh generators translate sound directly into geometry. The StructureSynth lane does something slightly different:

```text
captured WAV
    ↓
audio features / onset events
    ↓
EisenScript grammar
    ↓
StructureSynth or BrowserSynth
    ↓
OBJ export
    ↓
MeshLab / Blender / slicer
```

The goal is not a waveform object. The goal is a rule system whose growth behavior has been nudged by the recording.

## First command

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --template onset-lattice \
  --csv data/features/sine_sweep_features.csv \
  --seed 42 \
  --max-events 24
```

This writes:

```text
pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es
pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.json
data/features/sine_sweep_features.csv
```

The `.es` file is the StructureSynth grammar. The `.json` file is the receipt.

## What the current template does

The starter templates are:

- `onset-lattice`
- `radial-burst`
- `helix-coil`
- `helix-thread`
- `helix-vine`

It maps sound into StructureSynth like this:

| Captured WAV feature | EisenScript / StructureSynth behavior |
|---|---|
| RMS / loudness | trunk scale, branch step, object size |
| onset peaks | event calls placed across the structure |
| spectral centroid | low/mid/high event families, rotation bias |
| spectral bandwidth | twist, roughness, branching spread |
| seed | StructureSynth `set seed` value |
| max events | number of event calls written into `rule start` |

The spiral templates now split in two useful directions:

- `helix-coil`: more open, event-clustered spiral growth
- `helix-thread`: a tighter sequential path where events are threaded along one recursive body
- `helix-vine`: a more continuous spiral spine with smaller ribs, pulses, and side growths attached along it

## Recommended manual workflow

1. Generate the `.es` file with `dspform ssynth`.
2. Open the grammar in StructureSynth or BrowserSynth.
3. Render/build the structure.
4. Export OBJ.
5. Save exported OBJ into `pipelines/structuresynth/exports/` or `outputs/obj/`.
6. Open the OBJ in Blender for visual review.
7. Open the OBJ in MeshLab for mesh inspection and possible cleanup.
8. If printing, preserve both the raw exported OBJ and the repaired/print-oriented mesh.

## Why StructureSynth gets its own lane

StructureSynth is strongest where recursion, branching, rule weighting, and repeated primitive growth matter. It gives this repo an architectural and organismic channel that the direct Python mesh generators do not fully cover.

```text
Python generators:
  the sound becomes a surface/body.

StructureSynth generators:
  the sound becomes a set of growth instructions.
```

That distinction matters. This lane is for sonic scaffolds, roots, antennas, ruins, lattices, swarm-growth forms, and impossible little machines.

## Validation notes

The generated grammar is meant to be editable. After generation, try hand-changing:

- `set maxdepth`
- `set maxobjects`
- the first `{ s ... } trunk` call
- event rule names in `rule start`
- `rz`, `ry`, and `s` values inside event calls
- rule weights, once you begin writing ambiguous rules by hand

Keep successful hand-edits by saving the grammar under a new name and recording notes in the matching manifest or a local lab notebook.
