# Prompts für Arenen (ab Stage 8)

Jede Arena ist ein Hintergrundbild aus dem Bildgenerator. Das Werkzeug verkleinert es auf 320 × 200 Pixel,
reduziert es auf 175 Farben und zerlegt es in höchstens 1.000 verschiedene 8 × 8-Kacheln (bei Bedarf werden
ähnliche Kacheln zusammengelegt). Format wie das Rio-Bild: Querformat 16:10, z. B. 1586 × 992.

Aufbau, damit Kämpfer und Anzeige gut lesbar bleiben (Maße bezogen auf 320 × 200):
- **Boden** im unteren Viertel (ab etwa y = 150), die Füße der Kämpfer stehen bei y = 190. Ruhiges, sich
  wiederholendes Muster, keine Figuren oder Gegenstände im Vordergrund.
- **Oben** (y 0–40) liegen Namen, Energiebalken und Zeit: dort ruhiger Himmel ohne helle Einzelheiten.
- **Mitte** (y 40–150): die Kulisse mit dem Wahrzeichen, gern etwas zur Seite gerückt, damit die Kämpfer in
  der Bildmitte nicht vor dem hellsten Punkt stehen.
- Keine Menschen im Bild, kein Text, keine Schrift auf Schildern, kein Logo, kein Rahmen.
- Ablage: `assets/art/arena/<name>_source.png`.

## Konrad – Zeche Zollverein, Essen (`zollverein_source.png`)
```
A 16-bit era arcade fighting game stage background in detailed pixel art (Street Fighter II / Neo Geo style), landscape 16:10, side view, no characters.
Location: the UNESCO world heritage site Zeche Zollverein in Essen, Germany, at dusk. Right of the centre stands the famous Shaft XII headframe: the red-rust steel double-trestle winding tower (Doppelbock-Fördergerüst) with its two large spoked winding wheels on top, exactly as the real landmark. Around it the Bauhaus-style industrial halls of red-brown brick with flat roofs, long rows of steel-framed windows (some warmly lit from inside), steel girders, a conveyor bridge between two buildings and a tall brick chimney in the distance.
Sky: calm evening sky from deep violet at the top to warm orange near the horizon, a few soft clouds, the headframe and the halls dark against it; keep the top fifth of the picture calm and free of bright details.
Foreground floor (the bottom quarter of the picture): the wide paved yard in front of the halls - dark grey cobblestones in an even, repeating pattern with two old embedded rail tracks running horizontally across the whole width, slightly lit by the evening light. Nothing standing on the floor.
Large, clear shapes, big areas of flat colour with simple dithering rather than fine noise or tiny details; strong dark outlines; the same art style and lighting mood as a classic 1990s arcade fighter stage.
No people, no text, no letters, no signs with writing, no logo, no watermark, no border, no UI.
```
Anhang (optional, für den gleichen Stil): das Rio-Bild `assets/art/arena/rio_source.png` mit dem Zusatz
„Use the attached picture only as a reference for the pixel-art style, colour depth and composition (floor
height, calm sky at the top), not for its content.“

## Malee – Wat Arun, Bangkok (`watarun_source.png`)
```
A 16-bit era arcade fighting game stage background in detailed pixel art (Street Fighter II / Neo Geo style), landscape 16:10, side view, no characters.
Location: Bangkok, Thailand, at dusk on the bank of the Chao Phraya river. Left of the centre, across the river, the famous temple Wat Arun (Temple of Dawn): its tall central prang tower with steep stepped tiers decorated with coloured porcelain, flanked by smaller prangs, softly lit in warm golden light, exactly as the real landmark. On the far bank a few traditional Thai roofs with steep layered gables in red and gold, palm trees, a distant row of city lights. On the calm river a few small lantern reflections; no boats in front.
Sky: calm evening sky from deep violet at the top to warm orange and pink near the horizon, a few soft clouds; keep the top fifth of the picture calm and free of bright details.
Foreground floor (the bottom quarter of the picture): a wide wooden riverside pier deck of dark teak planks running horizontally across the whole width in an even, repeating pattern, with a low red-and-gold wooden railing only at the far edge of the deck towards the river. Nothing standing on the floor.
Large, clear shapes, big areas of flat colour with simple dithering rather than fine noise or tiny details; strong dark outlines; the same art style and lighting mood as a classic 1990s arcade fighter stage.
No people, no text, no letters, no signs with writing, no logo, no watermark, no border, no UI.
```
Anhang (optional, für den gleichen Stil): `assets/art/arena/rio_source.png` mit dem Zusatzsatz wie bei
Zollverein.
