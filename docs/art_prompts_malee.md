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
