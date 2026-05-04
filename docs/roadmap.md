# Roadmap

## Current snapshot

Local proof of pipeline is now real, not theoretical:

- [x] Local `.venv` workflow established.
- [x] First terrain run from a real WAV.
- [x] First vessel run from a real WAV.
- [x] First helix run from a real WAV.
- [x] Feature CSV + manifest export confirmed.
- [x] Parameter sweep confirmed on `helix.turns`.
- [x] Blender inspection still needs to be done manually.
- [x] Slicer inspection still needs to be done manually.
- [ ] First physical print still needs to be done.
- [ ] Notes from mesh/print review still need to be captured.

## Phase 1 — first body

- [x] Install Python environment.
- [x] Generate sample WAV.
- [x] Generate first spectrogram terrain OBJ.
- [x] Open in Blender.
- [x] Open in slicer.
- [ ] Print a small tile.
- [ ] Save notes.

## Phase 2 — direct grammars

- [x] Terrain tile.
- [x] Waveform ribbon.
- [x] Circular vessel.
- [x] Helical body.
- [x] Feature CSV export.
- [x] Manifest export.
- [ ] Preview render script.
- [x] Compare the first four lanes in Blender/MeshLab and record which ones feel least chart-like.

## Phase 3 — seeded families

- [x] Batch generator.
- [x] Contact-sheet preview.
- [x] Seed sweep.
- [x] Parameter sweep.
- [x] Comparison CSV.
- [x] First helix turns sweep from a real WAV.
- [ ] Stable local preview image generation in this environment.

## Phase 4 — controller-driven forms

- [ ] Read MIDI CC log.
- [ ] Read OSC/control CSV.
- [ ] Map controls to geometry parameters.
- [ ] Record performance trace.
- [ ] Generate mesh family from trace.

## Phase 4.5 — StructureSynth grammar bodies

- [x] Generate first `.es` grammar from WAV using `dspform ssynth`.
- [x] Open grammar in StructureSynth or BrowserSynth.
- [x] Export OBJ.
- [x] Save raw export beside grammar and manifest.
- [x] Inspect in Blender/MeshLab.
- [x] Compare three settings: seed, max events, onset threshold.
- [ ] Decide which objects are print candidates and which are render-only.

## Phase 5 — print lab

- [ ] Mesh repair presets.
- [ ] Slicer profile notes.
- [ ] Material log.
- [ ] Failed print archive.
- [ ] Student-safe checklist.
- [ ] Record whether terrain / vessel / helix survive first plastic contact.

## Phase 6 — installation/live lane

- [ ] Processing sketch export.
- [ ] TouchDesigner sketch notes.
- [ ] Live OSC/MIDI routing.
- [ ] Performance capture → mesh archive.
