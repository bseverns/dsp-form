/*
  DSP Form Lab — Processing OBJ export sketch

  This is a teaching/live-sketch lane, not the main Python pipeline.

  Requires the Nervous System OBJExport library:
  https://n-e-r-v-o-u-s.com/tools/obj/

  Goal:
  - Draw a simple waveform-like ribbon in Processing.
  - Press 'e' to export a single OBJ.

  Note:
  This is a starter sketch. For real audio input, add Minim, Processing Sound,
  or a CSV/OSC input path.
*/

import nervoussystem.obj.*;

boolean exportNextFrame = false;
float t = 0;

void setup() {
  size(900, 700, P3D);
}

void draw() {
  background(245);
  lights();
  translate(width/2, height/2, -120);
  rotateX(PI/3);
  rotateZ(t * 0.2);

  if (exportNextFrame) {
    beginRecord("nervoussystem.obj.OBJExport", "waveform_ribbon_processing.obj");
  }

  drawRibbon();

  if (exportNextFrame) {
    endRecord();
    exportNextFrame = false;
    println("Exported waveform_ribbon_processing.obj");
  }

  t += 0.01;
}

void drawRibbon() {
  noStroke();
  fill(180);

  int steps = 220;
  float length = 520;
  float w = 18;

  beginShape(QUAD_STRIP);
  for (int i = 0; i < steps; i++) {
    float u = i / float(steps - 1);
    float x = map(u, 0, 1, -length/2, length/2);
    float amp = sin(u * TWO_PI * 7.0 + t) * 80 + sin(u * TWO_PI * 23.0) * 20;
    float z = cos(u * TWO_PI * 5.0 + t * 0.7) * 50;
    vertex(x, amp - w, z);
    vertex(x, amp + w, z);
  }
  endShape();
}

void keyPressed() {
  if (key == 'e' || key == 'E') {
    exportNextFrame = true;
  }
}
