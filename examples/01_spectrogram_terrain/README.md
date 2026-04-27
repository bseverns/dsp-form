# Example 01 — Spectrogram Terrain

Generate a small test WAV and turn it into a relief tile.

```bash
dspform sample --out audio/samples/sine_sweep.wav

dspform terrain audio/samples/sine_sweep.wav \
  --out outputs/obj/sine_sweep_terrain.obj \
  --csv data/features/sine_sweep_features.csv \
  --width 90 \
  --depth 60 \
  --height 14 \
  --base 2
```

Open the OBJ in Blender or MeshLab. Then try a slicer.

Reflection:

- Does it read as landscape, graph, relief, or fossil?
- What changes if height is reduced by half?
- What changes if the depth is stretched?
