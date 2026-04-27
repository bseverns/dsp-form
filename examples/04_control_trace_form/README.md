# Example 04 — Control Trace Form

Future example: use a MIDI/OSC/WebSerial control trace to drive geometry parameters.

Possible CSV format:

```csv
time_seconds,cc01,cc02,cc03,cc04,button01,envelope01
0.000,0.2,0.4,0.1,0.8,0,0.05
0.016,0.2,0.4,0.1,0.8,0,0.06
```

Possible mappings:

```text
cc01 → height
cc02 → smoothing
cc03 → twist
cc04 → ridge depth
button01 → freeze/export marker
envelope01 → swelling or rib thickness
```

This is the natural bridge to MOARkNOBS-42 and other controller/DSP systems.
