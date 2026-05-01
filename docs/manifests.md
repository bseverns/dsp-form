# Manifests

A manifest is a receipt for a generated object.

Minimum fields:

```json
{
  "created_utc": "2026-04-26T00:00:00+00:00",
  "generator": "terrain",
  "seed": 42,
  "seed_usage": "metadata_only",
  "parameters": {},
  "audio": {},
  "mesh": {},
  "provenance": {},
  "outputs": {}
}
```

## Why manifests matter

They make the object:

- Repeatable.
- Debuggable.
- Teachable.
- Citable.
- Comparable across parameter sweeps.

## Future additions

Add these later:

- Host machine name.
- Printer/slicer profile.
- Material used.
- Print result notes.
- Photo/render paths.
- License/attribution details for source audio.

Current manifests now include lightweight provenance:

- `provenance.git_commit` when available
- `provenance.python_version`
- `provenance.package_versions` for core dependencies

Seed behavior is now explicit per export:

- `seed_usage: metadata_only` means seed is recorded but does not affect geometry/grammar.
- `seed_usage: geometry_rng` means seed changes mesh geometry.
- `seed_usage: grammar_rng` means seed changes grammar generation.

Sweep commands now also write aggregate receipts:

- `*_seed_sweep.json` for seed families
- `*_param_sweep.json` for parameter sweeps
- `*_comparison.csv` for parameter-by-parameter comparison
- `contact-sheet` PNGs can be generated from either sweep index JSON


## StructureSynth manifests

The `ssynth` command writes a manifest beside the generated `.es` file. It records:

- source audio path
- analysis settings
- StructureSynth template
- seed
- onset threshold
- max event count
- summary feature statistics
- generated grammar parameters
- expected next step: open in StructureSynth/BrowserSynth and export OBJ

For this lane, the manifest documents the grammar score. The exported OBJ should either receive its own later manifest or be named so the connection remains obvious.
