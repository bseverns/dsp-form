/*
  Minimal hand-editable StructureSynth grammar for dsp-form-lab.
  Use this as a sanity check before generated grammars.
*/

set seed 1
set maxdepth 32
set maxobjects 1200
set background white

R1

rule R1 maxdepth 16 {
  { s 0.7 } sphere
  { x 0.85 rz 18 ry 9 s 0.93 } R1
  { x 0.65 rz -34 ry 16 s 0.76 } R2
}

rule R2 maxdepth 8 {
  { s 0.38 } box
  { x 0.55 rz 42 ry -12 s 0.82 } R2
}
