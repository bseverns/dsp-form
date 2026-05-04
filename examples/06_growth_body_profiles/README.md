# Example 06 — Growth Body Profiles

This example generates one growth-body fossil from the same WAV for each dynamic
profile. The source audio, seed, and core parameters stay fixed so the profile
is the main variable.

## Generate the set

```bash
dspform growth audio/samples/dspFORMtest.wav \
  --profile scar \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_scar.obj

dspform growth audio/samples/dspFORMtest.wav \
  --profile bloom \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_bloom.obj

dspform growth audio/samples/dspFORMtest.wav \
  --profile braid \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_braid.obj

dspform growth audio/samples/dspFORMtest.wav \
  --profile faultline \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_faultline.obj

dspform growth audio/samples/dspFORMtest.wav \
  --profile organ \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_organ.obj

dspform growth audio/samples/dspFORMtest.wav \
  --profile relic \
  --memory 0.92 \
  --event-threshold 0.64 \
  --branchiness 0.35 \
  --scar-depth 2.0 \
  --seed 42 \
  --out outputs/obj/growth_profiles/dspFORMtest_growth_relic.obj
```

Each run writes:

- an OBJ mesh in `outputs/obj/growth_profiles/`
- a sidecar manifest with generator, parameters, audio provenance, mesh report,
  and gesture summary

## Compare

Look at the six manifests together and compare:

- `mesh.extents`
- `mesh.vertex_count` and `mesh.face_count`
- gesture counts versus visible surface change
- how each profile turns the same event history into a different body
