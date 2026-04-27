# EisenScript DSP Mapping Notes

The StructureSynth lane turns features into grammar behavior.

This is the working translation table:

| DSP concept | Feature source | EisenScript target | Sculptural effect |
|---|---|---|---|
| loudness / body | RMS | `s`, trunk scale, branch step | larger, heavier growth |
| attacks / impacts | onset envelope | event calls in `rule start` | ribs, forks, nodes, scars |
| brightness | spectral centroid | `ry`, event family | upwardness, fine detail, angular bias |
| roughness / spread | spectral bandwidth | `rz`, branch decay, twist | tangledness, turbulence |
| repeatability | seed | `set seed` | reproducible variants |
| density | onset count | `set maxobjects`, event count | sparse vs crowded structure |

## Summary mode vs event mode

### Summary mode

A whole WAV becomes a small number of constants.

```text
mean RMS → trunk scale
mean centroid → branch angle
mean bandwidth → twist
onset density → maxobjects
```

This produces coherent, stable objects.

### Event mode

Important moments in the WAV become individual grammar calls.

```text
onset at 0.21 s → { x -10.2 rz -20 s 0.74 } eventLow
onset at 1.03 s → { x -2.7  rz 12  s 1.10 } eventMid
onset at 2.44 s → { x 8.3   rz 47  s 0.46 } eventHigh
```

This produces objects that feel more like fossilized performances.

## Rule family idea

Use three broad event families first:

```text
eventLow   = bass/body/root behavior
eventMid   = branch/fork/scaffold behavior
eventHigh  = sparkle/detail/surface behavior
```

This keeps the mapping legible while leaving room for hand editing.

## Practical caution

A grammar can generate a beautiful screen object that is a terrible print object. Treat StructureSynth exports as raw studio material. Do not skip inspection.

The safest first prints are:

- short lattices
- low-detail scaffolds
- objects with larger primitives
- exports with conservative `maxobjects`
- meshes repaired or simplified in MeshLab before slicing
