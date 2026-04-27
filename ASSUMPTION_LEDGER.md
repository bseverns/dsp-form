# Assumption Ledger

This project begins with a few explicit assumptions.

## A1 — OBJ is the studio exchange format

OBJ is treated as the baseline exchange format because it moves easily between Python, Blender, MeshLab, Processing-oriented workflows, and many other creative tools.

Status: useful starting assumption.

## A2 — STL/3MF are print targets, not the only truth

The mesh may begin as OBJ, then become STL or 3MF when the object is being prepared for fabrication.

Status: useful starting assumption.

## A3 — The first grammars should be legible

Terrain, ribbon, and vessel grammars are intentionally simple enough to explain to students and collaborators.

Status: useful starting assumption.

## A4 — Manifests are part of the artwork/tool

A generated object without source and parameter memory is too easy to mystify and too hard to teach.

Status: core commitment.

## A5 — Mesh repair is not neutral

Repair tools can make files printable while changing the object. Raw and repaired files should both be preserved.

Status: core commitment.

## A6 — Live systems come after batch systems

TouchDesigner, OSC, MIDI, Jetson, and installation workflows will be stronger after the Python batch pipeline proves the grammar.

Status: practical starting constraint.


## A7 — StructureSynth grammars are scores

A generated `.es` file is treated as a score for recursive structure, not as a finished mesh. The OBJ exported from StructureSynth or BrowserSynth is one performance of that score.

Status: useful framing assumption.

## A8 — Audio can control rules without becoming literal geometry

A captured WAV does not need to become a waveform surface. It can become recursion depth, event density, branching behavior, scale decay, and rule-family selection.

Status: central StructureSynth lane assumption.
