# Manifests

A manifest is a receipt for a generated object.

Minimum fields:

```json
{
  "created_utc": "2026-04-26T00:00:00+00:00",
  "generator": "terrain",
  "seed": 42,
  "parameters": {},
  "audio": {},
  "mesh": {},
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

- Git commit hash.
- Host machine name.
- Python package versions.
- Printer/slicer profile.
- Material used.
- Print result notes.
- Photo/render paths.
- License/attribution details for source audio.


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
