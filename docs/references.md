# References and Tool Pointers

These are starting points for the project’s technical spine.

## Audio feature extraction

- librosa feature documentation: https://librosa.org/doc/0.11.0/feature.html
- Spectral centroid docs: https://librosa.org/doc/main/generated/librosa.feature.spectral_centroid.html
- MFCC docs: https://librosa.org/doc/main/generated/librosa.feature.mfcc.html

Use these for RMS, spectral centroid, spectral bandwidth, spectral contrast, MFCCs, chroma, onset strength, and other feature families.

## Mesh creation and export

- trimesh documentation: https://trimesh.org/
- trimesh OBJ exchange: https://trimesh.org/trimesh.exchange.obj.html
- trimesh export docs: https://trimesh.org/trimesh.exchange.export.html

Use these for loading, checking, and exporting meshes in OBJ/STL/PLY/GLB and related formats.

## Implicit fields and marching cubes

- scikit-image marching cubes example: https://scikit-image.org/docs/0.25.x/auto_examples/edges/plot_marching_cubes.html
- scikit-image measure API: https://scikit-image.org/docs/stable/api/skimage.measure.html

Use these when turning 3D scalar fields into surface meshes.

## Blender scripting

- Blender Python Mesh API: https://docs.blender.org/api/current/bpy.types.Mesh.html
- Blender command-line arguments: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- Blender Geometry Nodes manual: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/index.html

Use Blender for preview scenes, rendering, material tests, and later procedural/Geometry Nodes experiments.

## Mesh repair and inspection

- MeshLab: https://www.meshlab.net/
- PyMeshLab filter list: https://pymeshlab.readthedocs.io/en/latest/filter_list.html

Use MeshLab/PyMeshLab for inspection, cleanup, hole closing, non-manifold checks, simplification, and repair.

## Processing / classroom live sketching

- Nervous System OBJExport page: https://n-e-r-v-o-u-s.com/tools/obj/
- OBJExport GitHub repo: https://github.com/nervoussystem/OBJExport

Use Processing when the point is live drawing, fast teaching, or a direct “draw it and export it” experience.

## TouchDesigner / installation lane

- TouchDesigner CHOP documentation: https://docs.derivative.ca/CHOP
- TouchDesigner MIDI In CHOP: https://docs.derivative.ca/MIDI_In_CHOP

Use TouchDesigner later for live audio/MIDI/control pipelines and installation contexts.

## StructureSynth / EisenScript grammar lane

- StructureSynth home: https://structuresynth.sourceforge.net/
- StructureSynth EisenScript reference: https://structuresynth.sourceforge.net/reference.php
- Ubuntu manpage / command reference mirror: https://manpages.ubuntu.com/manpages/focal/man1/structure-synth.1.html
- BrowserSynth GitHub: https://github.com/kronpano/BrowserSynth
- BrowserSynth live app: https://kronpano.github.io/BrowserSynth/
- PyMeshLab Structure Synth mesh creation filter: https://pymeshlab.readthedocs.io/en/latest/filter_list.html

Use these for recursive grammar bodies, EisenScript syntax, OBJ export notes, and possible browser-based StructureSynth experiments.
