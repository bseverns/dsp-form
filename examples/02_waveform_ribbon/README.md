# Example 02 — Waveform Ribbon

Generate a swept ribbon from the same sound.

```bash
dspform ribbon audio/samples/sine_sweep.wav \
  --out outputs/obj/sine_sweep_ribbon.obj \
  --length 120 \
  --width 8 \
  --thickness 1.2 \
  --height 32 \
  --lateral 24 \
  --twist 1.5
```

Try changing only `--twist`, then only `--thickness`.

Reflection:

- When does the ribbon become too fragile?
- Does twist make the sound feel more alive or less legible?
