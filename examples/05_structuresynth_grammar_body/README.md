# Example 05 — StructureSynth Grammar Body

This example uses a WAV file to generate an EisenScript grammar for StructureSynth.

## Generate the grammar

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --csv data/features/sine_sweep_features.csv \
  --seed 42 \
  --max-events 24
```

## Build the object

1. Open the `.es` file in StructureSynth or BrowserSynth.
2. Render/build the structure.
3. Export OBJ.
4. Save the export as:

```text
pipelines/structuresynth/exports/sine_sweep_onset_lattice.obj
```

## Inspect

Open the OBJ in Blender and MeshLab. Record whether it is:

- visually coherent
- too dense
- too fragile
- printable after repair
- better kept as a render-only object

## Remix prompt

Change exactly one of these and regenerate:

- `--seed`
- `--max-events`
- `--onset-threshold`

Then compare the resulting grammar and exported object.
