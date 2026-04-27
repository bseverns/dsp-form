# Geometry Grammars

A geometry grammar is a rule system for translating DSP behavior into form.

## 1. Spectrogram terrain

```text
time → X
frequency bin → Y
energy → Z
```

Best for:

- Relief tiles.
- Wall panels.
- Classroom demonstrations.
- Quick proof-of-pipeline tests.

Risk:

- Can look too much like a graph unless the scale, smoothing, and base form are handled carefully.

## 2. Waveform ribbon

```text
time → path along X
RMS/envelope → lateral motion
spectral centroid → vertical lift
onset strength → thickness/rib accent
```

Best for:

- Sculptural filaments.
- Audio tendrils.
- Scroll-like forms.
- Objects that feel like a sound moving through space.

Risk:

- Thin ribbons can become fragile or non-printable. Keep thickness visible and honest.

## 3. Circular vessel

```text
time → angle around circle
RMS → radius
centroid → brightness/lift/skin behavior
onset → ridges or scars
vertical layer → vessel height
```

Best for:

- Sonic pottery.
- Signal reliquaries.
- Families of related forms.
- Small objects that communicate well in photos.

Risk:

- Open vessels may not be watertight. Decide whether the object is for printing, rendering, or both.

## 4. Implicit field

```text
audio features → density field
field threshold → marching cubes surface
```

Best for:

- Organic forms.
- Blob/organism/root structures.
- Less literal sound-to-shape mappings.

Risk:

- Meshes can become heavy quickly. Start with low resolutions and strict manifests.


## 5. StructureSynth grammar body

```text
audio features → EisenScript grammar
RMS → scale / trunk mass
onset peaks → event calls
centroid → low/mid/high rule family and rotation bias
bandwidth → twist / spread / roughness
```

Best for:

- Recursive scaffolds.
- Sound-grown architectures.
- Coral, root, antenna, ruin, lattice, and swarm forms.
- Situations where the audio should become a behavior system rather than a literal mesh.

Risk:

- StructureSynth exports can become dense quickly. Preserve the `.es` source, export OBJ conservatively, and inspect before printing.
