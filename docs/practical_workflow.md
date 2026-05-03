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

## Current proven pass

The repo has now been exercised locally with a real WAV through multiple bodies:

- terrain
- vessel
- helix
- helix parameter sweep (`turns`)

That means the current practical threshold has shifted from "can this repo make one object?" to "which body best carries the signal, and which ones survive inspection?"

Useful comparison loop:

```bash
dspform terrain audio/samples/dspFORMtest.wav \
  --out outputs/obj/dspFORMtest_terrain.obj \
  --csv data/features/dspFORMtest_features.csv

dspform vessel audio/samples/dspFORMtest.wav \
  --out outputs/obj/dspFORMtest_vessel.obj

dspform helix audio/samples/dspFORMtest.wav \
  --out outputs/obj/dspFORMtest_helix.obj

dspform param-sweep audio/samples/dspFORMtest.wav \
  --generator helix \
  --param turns \
  --values 2.5,3.5,4.5 \
  --out-dir outputs/obj/param_sweeps \
  --name-prefix dspFORMtest
```

Next manual step:

- Open those outputs side by side and decide which grammar feels like a body and which still feels like a chart.

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
3. **Can it be repeated?** Same source + parameters generate the same result, with seed behavior defined by each lane's `seed_usage` manifest field.


## StructureSynth grammar loop

```text
1. Capture or choose a WAV.
2. Run `dspform ssynth` to generate an EisenScript grammar.
3. Open the `.es` file in StructureSynth or BrowserSynth.
4. Build/render the recursive structure.
5. Export OBJ.
6. Save the raw OBJ beside the generated grammar and manifest.
7. Inspect in Blender/MeshLab.
8. Repair or simplify only after preserving the raw export.
```

First pass:

```bash
dspform ssynth audio/samples/sine_sweep.wav \
  --out pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es \
  --csv data/features/sine_sweep_features.csv \
  --seed 42 \
  --max-events 24
```

This lane is strongest when the sound should behave like a growth instruction set: branch here, thicken there, fork when struck, shimmer when bright.

## Seed sweep loop

Generate a family quickly:

```bash
dspform seed-sweep audio/samples/sine_sweep.wav \
  --generator ribbon \
  --out-dir outputs/obj/seed_sweeps \
  --seed-start 0 \
  --seed-count 12 \
  --wobble-mm 0.8
```

Then compare the resulting `*_seed_sweep.json` index and manifests before picking print candidates.

## Parameter sweep loop

Compare one control directly:

```bash
dspform param-sweep audio/samples/sine_sweep.wav \
  --generator ssynth \
  --param max_events \
  --values 8,16,24,32 \
  --seed 42 \
  --out-dir outputs/param_sweeps
```

Use the generated `*_comparison.csv` to compare output paths, mesh metrics, and StructureSynth event counts across the sweep.

## Contact sheet loop

Turn any sweep into a visual board:

```bash
dspform contact-sheet outputs/obj/seed_sweeps/sine_sweep_ribbon_seed_sweep.json \
  --out outputs/previews/sine_sweep_ribbon_seed_sheet.png
```

For OBJ-based sweeps this renders quick mesh thumbnails. For grammar-only sweeps it falls back to labeled metadata cards.

In restricted environments, Matplotlib may need a writable config/cache directory for the first render pass. If preview generation stalls, set `MPLCONFIGDIR` to a writable temp folder and retry.
