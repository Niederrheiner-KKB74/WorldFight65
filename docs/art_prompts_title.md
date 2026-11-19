# Prompt für das Titelbild (Stage 6)

Das Titelbild wird wie die Arena verarbeitet: auf 320 × 200 Pixel verkleinert, auf 175 Farben reduziert und
in höchstens 1.000 verschiedene 8 × 8-Kacheln zerlegt. Ablegen als `assets/art/title/title_source.png`.
Den Schriftzug „WORLDFIGHT 65“ und „PRESS FIRE“ setzt das Spiel selbst mit seiner Schrift darüber – das Bild
soll **keinen Text** enthalten (Generatoren schreiben Buchstaben unzuverlässig).

```
A 16-bit era arcade fighting game title screen illustration in detailed pixel art (Street Fighter II / Neo Geo style), landscape 16:10.
Theme: a fighting "world championship". In the centre background a huge glowing globe or a stylised world map in warm sunset colours, with light rays behind it. In the foreground, at the bottom left and bottom right, the two fighters from the attached master images stand facing each other in their fighting stances, seen from a low angle, cut off at the knees: on the left Tiago (Brazilian capoeira fighter, white capoeira trousers, green-yellow cord belt, bare muscular torso), on the right Konrad (German Greco-Roman wrestler, black wrestling singlet with black-red-gold side stripes, blond buzz cut and beard). Keep both exactly as in the attached master images (faces, costumes, colours).
Keep the upper third of the picture (above the globe) calm and dark - a dark purple-to-orange evening sky - because the game writes its own title logo there, and keep a calm band in the lower middle between the two fighters for the "PRESS FIRE" text.
Large, clear shapes and big areas of flat colour with simple dithering rather than fine noise or tiny details; strong dark outlines.
No text, no letters, no logo, no numbers, no watermark, no border, no UI.
```

Anhänge: die beiden Master-Bilder `assets/art/tiago/master.png` und `assets/art/konrad/master.png`.

Hinweis zur Kachelgrenze: Je ruhiger große Flächen sind (Himmel, Globus), desto weniger verschiedene Kacheln
braucht das Bild. Das Rio-Bild kam auf 996 von 1.000; bei mehr Kacheln rechnet das Werkzeug ähnliche Kacheln
zusammen (ab Stage 6, wenn nötig) – dabei verliert das Bild etwas Feinheit.
