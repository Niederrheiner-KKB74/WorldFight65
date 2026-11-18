# Prompts für die Spezialangriffe (Stage 5)

Je Kämpfer ein Sheet `sp1.png` mit **4 Zellen** (das Spiel zeigt sie als 1, 2, 2, 3, 4). Bis das Sheet da ist,
nimmt das Spiel Platzhalter-Frames: Tiago aus `hk`, Konrad aus `hp`.
Anhänge jeweils: 1. das Master-Bild des Kämpfers, 2. die Posen-Vorlage (`assets/art/guides/`).
Ablegen als `assets/art/<kämpfer>/sp1.png`; Prüfung mit `tools/check_sheets.py`, Import über `tools/build.py`.

## Tiago – Meia-lua de compasso (4 Frames) – Vorlage `tiago_sp1_guide.png`
```
Edit the first attached image (the master sprite of Tiago): keep the character exactly as he is - the same face, hair, body, costume, colours, pixel-art style and the same scale. Draw him in the 4 poses of the second attached image, a pose guide with 4 mannequins, one per frame, from left to right.
In the mannequins, the ORANGE arm and leg are his LEAD arm and leg (the front ones, towards the opponent on the right), the BLUE arm and leg are his REAR arm and leg. Match the positions of hands, feet, knees, elbows, hips and the lean of the torso as closely as possible; the mannequin is only a stick figure, so give him his real body, costume and muscles.
Animation: his special move, the capoeira "meia-lua de compasso", a spinning heel kick with the hands on the floor. 1: he turns and bends deep forward, the lead hand reaching for the floor next to the lead foot, the rear foot about to leave the floor. 2: both hands are on (or just above) the floor, head low near the lead knee, the REAR leg swings straight up behind him in a wide arc. 3: impact - the rear leg has swung over and forward, almost straight, the HEEL in front of him at chest height of the opponent; head and hands still low. 4: he comes back up into the guard. The dashed grey arrows in the guide only show the path of the rear foot - do not draw them.
Output: one sprite sheet, a single row of 4 cells of exactly 256 x 256 px (image 1024 x 256 px), solid flat magenta background #FF00FF, no shadow, no text, no frame numbers, no motion lines, no magenta, pink or purple on the character. Facing right. Feet (the standing foot) on the floor at y = 239 (the black line in the guide). Same size as the master in every frame - never enlarge or shrink him.
```

## Konrad – Rammbock (4 Frames) – Vorlage `konrad_sp1_guide.png`
```
Edit the first attached image (the master sprite of Konrad): keep the character exactly as he is - the same face, hair, body, costume, colours, pixel-art style and the same scale. Draw him in the 4 poses of the second attached image, a pose guide with 4 mannequins, one per frame, from left to right.
In the mannequins, the ORANGE arm and leg are his LEAD arm and leg (the front ones, towards the opponent on the right), the BLUE arm and leg are his REAR arm and leg. Match the positions of hands, feet, knees, elbows, hips and the lean of the torso as closely as possible; the mannequin is only a stick figure, so give him his real body, costume and muscles.
Animation: his special move "Rammbock", a wrestler's running shoulder charge. 1: he drops his LEAD shoulder, upper body bent forward, both fists tucked in front of his chest, knees bent. 2: he drives forward hard off the rear foot - long stride, rear leg stretched far behind, lead foot planted in front, torso leaning strongly forward, lead shoulder and upper arm in front like a battering ram, chin tucked. 3: impact - the lead shoulder at chest height of the opponent, body leaning even further into it, rear heel up. 4: back upright in the guard. The dashed grey arrows in the guide only show the direction of the charge - do not draw them.
Output: one sprite sheet, a single row of 4 cells of exactly 256 x 256 px (image 1024 x 256 px), solid flat magenta background #FF00FF, no shadow, no text, no frame numbers, no motion lines, no magenta, pink or purple on the character. Facing right. Feet on the floor at y = 239 (the black line in the guide). Same size as the master in every frame - never enlarge or shrink him.
```
