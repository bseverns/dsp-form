# Mesh Health Checklist

Before printing, check the mesh.

## Basic checks

- [ ] Opens in Blender or MeshLab.
- [ ] Correct scale in millimeters.
- [ ] Not absurdly large or tiny.
- [ ] Face count is reasonable.
- [ ] No obvious missing walls.
- [ ] No inverted-looking surfaces.
- [ ] No needle-thin unsupported features.
- [ ] Base or contact surface is printable.

## Print checks

- [ ] Slicer imports without repair warnings.
- [ ] Slicer preview shows expected layers.
- [ ] First layer has enough contact area.
- [ ] Thin walls exceed nozzle capability.
- [ ] Overhangs are acceptable or supports are intentional.
- [ ] Print time is appropriate for an experiment.

## Aesthetic checks

- [ ] The form still feels linked to the signal.
- [ ] The mapping is explainable.
- [ ] The object is not merely decorative noise.
- [ ] The manifest is enough to regenerate or critique it.

## Keep raw and repaired files

Always preserve:

```text
form.raw.obj
form.cleaned.obj
form.print.stl
form.manifest.json
```

Mesh repair is not neutral. It can save a print and damage an artwork. Keep both histories.
