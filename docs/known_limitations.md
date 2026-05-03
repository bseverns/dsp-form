# Known Limitations

This starter repo is intentionally modest.

## Current limits

- The Python generators are first-pass grammars, not final sculpture systems.
- STL/3MF export is planned but not yet wired into the CLI.
- Mesh repair is optional and conservative.
- Blender rendering is provided as a script, not as a fully polished preview system.
- Contact-sheet rendering depends on Matplotlib and may need a writable `MPLCONFIGDIR` on first run in locked-down environments.
- Processing sketch is a teaching stub, not a full audio input system.
- Control trace input is documented but not yet implemented.
- StructureSynth grammar generation is implemented as a starter score writer, not as an automated StructureSynth renderer/exporter.

## Design choice

The repo starts with plain, inspectable code instead of a clever abstraction layer. That is intentional. The first goal is to make the pipeline understandable enough to teach, debug, and extend.

The repo has now proven that several direct-mesh lanes can run locally from a real WAV, but that is not the same as print validation. Physical review, slicer behavior, and repair discipline remain external steps.


## StructureSynth-specific limits

- The repo can generate `.es` grammar files, but the actual StructureSynth/BrowserSynth OBJ export remains a manual step.
- Generated EisenScript should be treated as editable studio material.
- Grammar-heavy exports may contain many primitives and can be slow or fragile in Blender/slicers.
- Printability depends on export settings, primitive size, mesh cleanup, and final scale.
