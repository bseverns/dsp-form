/*
  Onset Lattice template for dsp-form-lab.
  Copy this into StructureSynth or BrowserSynth, then replace the placeholder
  values with generated or hand-tuned values.
*/

set seed {{ seed }}
set maxdepth {{ maxdepth }}
set maxobjects {{ maxobjects }}
set background white

start

rule start {
  { s {{ trunk_scale }} } trunk
  {{ event_calls }}
}

rule trunk maxdepth {{ trunk_depth }} {
  { s {{ trunk_body_scale }} } sphere
  { x {{ trunk_step }} rz {{ trunk_twist }} ry {{ trunk_lift }} s {{ trunk_decay }} } trunk
  { x {{ branch_step }} rz {{ branch_angle }} ry {{ branch_lift }} s {{ branch_decay }} } branch
}

rule branch maxdepth {{ branch_depth }} {
  { s {{ branch_body_scale }} } box
  { x {{ branch_step }} rz {{ branch_angle }} ry {{ branch_lift }} s {{ branch_decay }} } branch
  { x {{ twig_step }} rz {{ twig_angle }} s {{ twig_decay }} } twig
}

rule twig maxdepth {{ twig_depth }} {
  { s {{ detail_scale }} } sphere
  { x {{ twig_step }} rz {{ twig_angle }} ry {{ twig_lift }} s {{ twig_decay }} } twig
}

rule eventLow maxdepth 6 {
  { s {{ low_scale }} } sphere
  { x {{ low_step }} rz {{ low_twist }} ry {{ low_lift }} s 0.82 } eventLow
}

rule eventMid maxdepth 7 {
  { s {{ mid_scale }} } box
  { x {{ mid_step }} rz {{ mid_twist }} ry {{ mid_lift }} s 0.80 } eventMid
  { x 0.54 rz {{ mid_branch_angle }} s 0.70 } twig
}

rule eventHigh maxdepth 5 {
  { s {{ high_scale }} } sphere
  { x {{ high_step }} rz {{ high_twist }} ry {{ high_lift }} s 0.72 } eventHigh
  { x 0.35 rz {{ high_sparkle_angle }} s 0.54 } sparkle
}

rule sparkle maxdepth 2 {
  { s {{ sparkle_scale }} } sphere
}
