# Control Mapping Notes

This project can eventually accept control traces from MIDI, OSC, WebSerial, or CSV logs.

## Possible control sources

- MIDI CC values from a knob controller.
- OSC messages from Processing, TouchDesigner, Max, Ableton, or custom scripts.
- WebSerial logs from a browser-based controller/configurator.
- Envelope follower CSVs from an audio/DSP experiment.
- SeedBox-style deterministic parameter logs.

## Starter mapping table

| Control | Geometry parameter | Result |
|---|---|---|
| cc01 | height scale | taller/shorter forms |
| cc02 | smoothing | calmer or more jagged surfaces |
| cc03 | twist | ribbon/vessel torsion |
| cc04 | radial amplitude | stronger/weaker body swelling |
| cc05 | ridge depth | beat/event emphasis |
| cc06 | decimation target | dense/sparse mesh |
| button01 | freeze marker | export moment |
| envelope01 | thickness | live swelling |

## Practical first trace format

```csv
time_seconds,cc01,cc02,cc03,cc04,button01,envelope01
0.000,0.20,0.40,0.10,0.80,0,0.05
0.016,0.22,0.40,0.10,0.80,0,0.06
```

A future parser can resample this trace to match audio frames or use it directly as the geometry timeline.


## StructureSynth controls

The same control traces can generate EisenScript grammar variations.

| Control | EisenScript / grammar target | Result |
|---|---|---|
| cc01 | `set maxdepth` or trunk recursion depth | longer/shorter growth |
| cc02 | `set maxobjects` / event count | sparse/dense structures |
| cc03 | `rz` / twist values | spiral or torsional behavior |
| cc04 | branch decay / `s` values | compact vs spreading bodies |
| cc05 | event family mix | low/mid/high growth emphasis |
| button01 | grammar snapshot | freeze/export a score |
| envelope01 | event scale | swelling nodes or ribs |

A useful future performance mode: record MOARkNOBS/MIDI/OSC values as a CSV, then generate several `.es` grammars from marked moments in the take.
