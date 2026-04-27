# Practical Workflow

## Baseline loop

```text
1. Choose or generate a WAV.
2. Extract starter features.
3. Generate a mesh using one grammar.
4. Export OBJ.
5. Inspect mesh dimensions and face/vertex count.
6. Open in Blender or MeshLab.
7. Repair/simplify only if needed.
8. Slice a small test print.
9. Save manifest and notes.
```

## First command-line pass

```bash
dspform sample --out audio/samples/sine_sweep.wav

dspform terrain audio/samples/sine_sweep.wav \
  --out outputs/obj/sine_sweep_terrain.obj \
  --csv data/features/sine_sweep_features.csv
```

Then inspect the OBJ in:

- Blender for composition/rendering.
- MeshLab for mesh cleanup and inspection.
- Cura/PrusaSlicer/Bambu Studio/etc. for print feasibility.

## Small print discipline

Do not begin with heroic prints.

Start with:

- 60–90 mm terrain tiles.
- 80–120 mm ribbons.
- 60–90 mm vessels.
- 0.2 mm layer height.
- PLA.
- Known-good printer profile.

The early object should answer:

> Does the mapping survive contact with plastic?

## Three validation questions

1. **Can it be opened?** OBJ imports cleanly in Blender or MeshLab.
2. **Can it be understood?** A human can explain which feature shaped which dimension.
3. **Can it be repeated?** Same source + seed + parameters generate the same result.
