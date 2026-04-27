# StructureSynth Pipeline

This folder holds the grammar-based lane for DSP Form Lab.

The core idea:

```text
captured WAV → features → generated EisenScript → StructureSynth/BrowserSynth → OBJ export
```

Use this when the sound should become a **rule system** rather than a direct mesh surface.

## Folders

```text
grammars/templates/   hand-written starter grammars and notes
grammars/generated/   generated .es files; safe to delete/regenerate
exports/              OBJ/GLTF exports from StructureSynth or BrowserSynth
presets/              JSON presets for repeatable mappings
scripts/              small helper scripts/wrappers
```

## Starter command

From the repo root:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --seed 42 \
  --max-events 24
```

Then open the `.es` file in StructureSynth or BrowserSynth and export OBJ.

## Keep both files

When you export from StructureSynth, keep:

```text
source grammar: .es
exported mesh: .obj
sidecar receipt: .json
```

The grammar is the score. The OBJ is one performance of it.
