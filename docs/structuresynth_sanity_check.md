# StructureSynth / EisenScript Sanity Check

This note records the assumptions used by the StructureSynth lane.

## Conservative syntax target

The generated grammars intentionally use a small, boring subset of EisenScript:

```text
set seed <integer>
set maxdepth <integer>
set maxobjects <integer>
set background <color>

start

rule start {
  { x <float> y <float> z <float> rx <float> ry <float> rz <float> s <float> } someRule
}

rule someRule maxdepth <integer> {
  { s <float> } sphere
  { x <float> rz <float> s <float> } someRule
}
```

The generated files avoid:

- preprocessor directives such as `#define`
- color pools
- custom mesh/triangle declarations
- rule successor syntax using `>`
- rule-name underscores
- template placeholders in executable `.es` files

This is meant to keep the output compatible with older StructureSynth builds and browser ports.

## Files to test first

1. `pipelines/structuresynth/grammars/templates/minimal_audio_branch.es`
2. `pipelines/structuresynth/grammars/templates/onset_lattice_static_example.es`
3. A generated grammar from `dspform ssynth`

## Known uncertainty

The starter repo cannot fully validate StructureSynth output without StructureSynth or BrowserSynth installed locally. Treat the included linter as a smoke test, not a replacement for opening the `.es` file and building it.
