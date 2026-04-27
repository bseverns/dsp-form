/*
  Static executable StructureSynth/EisenScript example for dsp-form-lab.

  This file is deliberately conservative:
  - no preprocessor defines
  - no color pools
  - no rule-name underscores
  - no generated template placeholders
  - only standard transforms, recursive rules, sphere, and box

  It is meant as the first paste/build sanity check before using generated
  WAV-derived grammars.
*/

set seed 42
set maxdepth 36
set maxobjects 2200
set background white

start

rule start {
  { s 1.2 } trunk
  { x -5 y 1 z 1 rz -28 ry 15 s 0.9 } eventHigh
  { x 0 y 0 z 1.4 rz 8 ry 0 s 1.0 } eventMid
  { x 5 y -1 z 1.8 rz 32 ry -15 s 1.1 } eventLow
}

rule trunk maxdepth 14 {
  { s 0.64 } sphere
  { x 0.95 rz 10 ry 8 s 0.94 } trunk
  { x 0.68 rz -30 ry 20 s 0.78 } branch
  { x 0.62 rz 28 ry -16 s 0.74 } branch
}

rule branch maxdepth 9 {
  { s 0.42 } box
  { x 0.62 rz 27 ry 9 s 0.78 } branch
  { x 0.5 rz -22 ry -7 s 0.68 } twig
}

rule twig maxdepth 5 {
  { s 0.18 } sphere
  { x 0.42 rz 18 ry 10 s 0.72 } twig
}

rule eventLow maxdepth 5 {
  { s 0.95 } sphere
  { x 0.9 rz -22 ry 12 s 0.8 } eventLow
}

rule eventMid maxdepth 5 {
  { s 0.58 } box
  { x 0.75 rz 24 ry 18 s 0.76 } eventMid
  { x 0.5 rz -22 s 0.66 } twig
}

rule eventHigh maxdepth 4 {
  { s 0.28 } sphere
  { x 0.55 rz 54 ry 26 s 0.7 } eventHigh
  { x 0.35 rz -58 s 0.5 } sparkle
}

rule sparkle maxdepth 2 {
  { s 0.1 } sphere
}
