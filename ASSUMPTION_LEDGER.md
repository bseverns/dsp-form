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
