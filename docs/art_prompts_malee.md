# Prompts für Malee (Stage 10)

Jeweils `assets/art/malee/master.png` anhängen. Einzelbilder sind in Ordnung (ein Bild pro Pose,
beliebige Größe, magenta Hintergrund): ich setze sie zusammen, bringe sie auf Master-Größe und Master-Farben.
Ablage der fertigen Sheets in `assets/art/malee/`, Rohbilder in `assets/art/source/`.

## block (1 Frame)
```
Edit the attached master sprite of Malee: keep the character exactly as she is - the same face, ponytail, headband, armbands, wraps, costume, the same colours, the same pixel-art style and the same scale. Only the pose changes.
Pose: standing block, Muay Thai style. Same stance and feet as in the master. Both forearms raised high and close together in front of her face (the wrapped fists at forehead height, elbows tight in front of the chest), chin tucked, eyes looking over the forearms. Both feet stay flat on the ground (no raised knee).
Output: one 256 x 256 px cell (or any square size), solid flat magenta background #FF00FF, no shadow, no text. No magenta, pink or purple on the character. Facing right, soles at y = 239, exactly as big as in the master.
```

## crouch (1 Frame)
```
Edit the attached master sprite of Malee: keep the character exactly as she is - the same face, ponytail, headband, armbands, wraps, costume, the same colours, the same pixel-art style and the same scale. Only the pose changes.
Pose: deep crouch with the guard up: knees deeply bent, feet a bit wider apart than in the master, both feet flat on the ground, upper body upright and leaning slightly forward, wrapped fists in front of the chin. Same scale as standing: crouching she is only about 150 px from soles to top of head; the upper part of the cell stays empty magenta. Do not enlarge her to fill the cell.
Output: one 256 x 256 px cell (or any square size), solid flat magenta background #FF00FF, no shadow, no text. No magenta, pink or purple on the character. Facing right, soles at y = 239.
```

## c_block (1 Frame) – zweiter Anhang: die fertige Hocke (`crouch`)
```
Edit the first attached image (the master sprite of Malee): keep the character exactly as she is - the same face, ponytail, headband, armbands, wraps, costume, the same colours, the same pixel-art style and the same scale. The second attached image shows her crouching: use exactly this crouch (legs, feet, height).
Pose: crouching block: in this crouch, both forearms raised close together in front of her face, fists at forehead height, chin tucked. She is as small as in the crouch image (about 150 px from soles to top of head); the upper part of the cell stays empty magenta.
Output: one 256 x 256 px cell (or any square size), solid flat magenta background #FF00FF, no shadow, no text. No magenta, pink or purple on the character. Facing right, soles at y = 239.
```

# Angriffe und übrige Animationen

Posen-Vorlagen: `assets/art/guides/malee_<anim>_guide.png` (alle Frames) und `malee_<anim>_<n>.png`
(ein Frame, 512 px). **Einzelbilder gehen am sichersten:** pro Frame ein Bild mit der Einzel-Vorlage.
Anhänge: 1. `master.png`, 2. bei Hock-Animationen `crouch.png`, sonst entfällt das, 3. die Vorlage.

## Vorlage für ein Einzelbild
```
Edit the first attached image (the master sprite of Malee): keep the character exactly as she is - the same face, ponytail, headband, armbands, wraps, costume, the same colours, the same pixel-art style and the same scale. The last attached image is a pose guide: a mannequin whose ORANGE arm and leg are her LEAD arm and leg (the front ones, towards the opponent on the right) and whose BLUE arm and leg are her REAR arm and leg. Match the positions of hands, elbows, feet, knees, hips and the lean of the torso as closely as possible; the mannequin is only a stick figure, so give her her real body, costume and muscles. Dashed grey arrows only show a movement - do not draw them.
Pose: <POSE>
Output: one image, solid flat magenta background #FF00FF, no shadow, no text, no motion lines. No magenta, pink or purple on the character. Facing right. Feet on the ground at the black line of the guide (airborne poses: as high as in the guide). Exactly as big as in the master - never enlarge or shrink her.
```
Für Hock-Animationen zusätzlich nach dem ersten Satz: „The second attached image shows her crouching: this
pose starts from this crouch and has its size (about 150 px from soles to top of head).“

## <POSE> je Animation und Frame
**lp** – Jab (3): 1 lead fist starts forward · 2 lead arm fully extended at head height, shoulder behind it ·
3 the fist comes back to the guard.

**hp** – Ellbogen, Sok (4): 1 rear elbow drawn back and up, body turned away a little · 2 rear elbow strikes
forward at head height, forearm horizontal across her face, hip and rear heel turned in · 3 follow-through,
elbow still in front · 4 back to the guard.

**lk** – Lowkick (3): 1 rear knee turns inwards, rear foot leaves the ground · 2 rear shin swings into the
opponent's thigh: rear leg almost straight, shin horizontal at knee height, arms in guard, lead heel turned ·
3 the rear foot comes back down behind her.

**hk** – Roundhouse (4): 1 rear knee rises in front · 2 the rear shin hits at head height, leg almost
straight, upper body leaning back, rear arm swinging down behind her for balance · 3 the leg swings through
in front of her, knee bent · 4 back to the stance.

**c_lp** – Hock-Jab (3), **c_lk** – Hock-Tritt (3, tief), **sweep** – Feger (4): wie die Vorlagen; aus der
Hocke heraus (zweiter Anhang).

**j_p** – Sprung-Schlag (3): 1 tucked in the air · 2 lead fist punches forward and down · 3 tucked again.

**j_k** – Knie im Sprung (3): 1 tucked in the air · 2 the rear knee drives forward and up, both hands
reaching forward as if to grab the opponent's neck · 3 tucked again.

**sp1** – Khao Loi, fliegendes Knie (4): 1 she pushes off the rear foot, body leaning forward · 2 in the
air, the rear knee rising in front, hands reaching forward · 3 impact: the knee at head height of the
opponent, both hands forward at head height (clinch), body leaning back · 4 landed, back in the guard.

**hit** – Treffer (2): 1 head and upper body thrown back, arms open · 2 recovering towards the guard.

**jump** (3): 1 crouched, ready to take off · 2 tucked in the air, knees pulled up · 3 landing, knees bent.

**fall** (3): 1 thrown backwards, arms flung up · 2 falling on her back · 3 lying flat on her back on the
ground, head to the left.

**getup** (2): 1 kneeling on the rear knee, one hand on the ground · 2 rising into a crouch with guard up.

**win** – Wai (2): 1 standing upright, palms pressed together in front of her chest, head slightly bowed ·
2 a small bow from the waist with the palms still together.
