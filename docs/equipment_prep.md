# Equipment Prep

## Authoring computer

Recommended setup:

- Modern MacBook Pro or M-series Mac mini for authoring.
- Python 3.10+.
- Git.
- Blender.
- MeshLab.
- Slicer software appropriate to the printer.
- Audio editor/DAW for trimming and preparing source files.

Older Intel Mac minis can become render/utility stations later. Raspberry Pi and Jetson boards are better treated as installation/live-control devices after the core pipeline works.

## Python environment

Install the repo in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional repair support:

```bash
pip install -e '.[repair]'
```

## Audio/DSP prep

Useful materials:

- Audio interface.
- Small microphone.
- Line cables.
- Headphones.
- Calibration tones.
- Short test WAVs.
- Control traces from MIDI/OSC/WebSerial if available.

Keep test material small at first. Four to ten seconds is plenty for development.

## Fabrication prep

Start with boring reliability:

- PLA.
- Known-good 0.4 mm nozzle.
- Conservative slicer profile.
- Calipers.
- A print log.
- A folder of failed exports and failed prints.

Failures are useful if they are labeled.
