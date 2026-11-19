#!/usr/bin/env python3
"""WorldFight65 music (Stage 6), composed by Claude as data: writes music/title.json and music/fight.json in
the format of docs/music_json.md (engine from ShooterMega65 Stage 19).

  python3 assets/source/compose_music.py

Each bar is one pattern of 16 rows (a row = a 16th note). Voice 1 melody, voice 2 arpeggio chords,
voice 3 bass and drums in turn (drums on the beats, bass between them).
- title: "Campeonato" - festive fanfare in C major with a samba-like syncopated bass, tempo 7 (~107 BPM),
  16 bars, loops from bar 1 (about 36 s).
- fight: "Copacabana Clash" - driving A minor, tempo 5 (150 BPM), 4 bars intro + 32 bars, loops after the
  intro (about 51 s).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']


def n(midi):
    """MIDI-like number (C-0 = 0) -> 'C-0'"""
    return f'{NAMES[midi % 12]}{midi // 12}'


def note(s):
    """'A-3' -> number"""
    return NAMES.index(s[:2]) + 12 * int(s[2])


INSTRUMENTS = {
    'lead':   {'wave': 'pulse', 'attack': 0, 'decay': 9, 'sustain': 9, 'release': 5, 'pulse': 1300,
               'pulse_sweep': 18, 'vibrato': {'delay': 10, 'speed': 2, 'depth': 2}},
    'brass':  {'wave': 'saw', 'attack': 1, 'decay': 8, 'sustain': 10, 'release': 5,
               'vibrato': {'delay': 12, 'speed': 2, 'depth': 3}},
    'arp_maj': {'wave': 'pulse', 'attack': 0, 'decay': 6, 'sustain': 6, 'release': 3, 'pulse': 900,
                'pulse_sweep': 14, 'arpeggio': [0, 4, 7, 12]},
    'arp_min': {'wave': 'pulse', 'attack': 0, 'decay': 6, 'sustain': 6, 'release': 3, 'pulse': 900,
                'pulse_sweep': 14, 'arpeggio': [0, 3, 7, 12]},
    'bass':   {'wave': 'pulse', 'attack': 0, 'decay': 7, 'sustain': 5, 'release': 2, 'pulse': 2200,
               'pulse_sweep': -20},
    'kick':   {'attack': 0, 'decay': 7, 'sustain': 0, 'release': 0,
               'wave_table': [['pulse', 'G-3'], ['triangle', 'C-3'], ['triangle', 'G-2'], ['triangle', 'D-2'],
                              ['triangle', 'A-1']]},
    'snare':  {'attack': 0, 'decay': 8, 'sustain': 0, 'release': 0,
               'wave_table': [['noise', 'C-7'], ['pulse', 'D-3'], ['noise', 'A-6'], ['noise', 'F-6'],
                              ['noise', 'D-6']]},
    'hat':    {'attack': 0, 'decay': 3, 'sustain': 0, 'release': 0, 'wave_table': [['noise', 'C-7']]},
}


def chord_quality(name):
    return 'arp_min' if name.endswith('m') else 'arp_maj'


def chord_root(name, octave):
    return note(name.rstrip('m').ljust(2, '-')[:2] + str(octave))


def arp_bar(ch, octave, rhythm):
    """arpeggio voice: the chord struck on the rows of rhythm, released before the next strike"""
    rows = ['...'] * 16
    inst = chord_quality(ch)
    r = n(chord_root(ch, octave))
    for k in rhythm:
        rows[k] = f'{r} {inst}'
    return rows


def bass_bar(ch, style):
    """voice 3: drums on fixed rows, bass notes between them"""
    root = chord_root(ch, 2)
    fifth = root + 7
    if style == 'samba':        # surdo-like: kick on 1, snare on 3, syncopated bass
        hits = {0: 'kick', 8: 'kick', 4: 'snare', 12: 'snare', 14: 'hat'}
        bass = {3: root, 6: fifth, 10: root, 11: root + 12}
    else:                       # driving rock: kick, bass eighths, snare on 2 and 4
        hits = {0: 'kick', 4: 'snare', 8: 'kick', 12: 'snare', 15: 'hat'}
        bass = {2: root, 3: root, 6: root + 12, 7: root, 10: fifth, 11: root, 14: root + 12}
    rows = ['...'] * 16
    for k, d in hits.items():
        rows[k] = f'C-4 {d}'
    for k, v in bass.items():
        rows[k] = f'{n(v)} bass'
    return rows


def melody_bar(notes, inst):
    """notes: list of (row, 'A-4' or 'off', tie) for one bar"""
    rows = ['...'] * 16
    first = True
    for item in notes:
        k, v = item[0], item[1]
        if v == 'off':
            rows[k] = 'off'
            continue
        rows[k] = f'{v} {inst}' if first else v
        first = False
        if len(item) > 2 and item[2]:
            rows[k] += ' >'
    return rows


def piece(name, title, tempo, volume, bars, intro_bars, style, lead, arp_octave, arp_rhythm):
    """bars: list of (chord, melody notes); intro_bars: how many bars before the loop point"""
    pats, o1, o2, o3 = {}, [], [], []

    def add(prefix, rows):
        for k, v in pats.items():          # reuse identical patterns
            if v == rows and k.startswith(prefix):
                return k
        k = f'{prefix}{len(pats)}'
        pats[k] = rows
        return k
    for ch, mel in bars:
        o1.append(add('m', melody_bar(mel, lead) if mel else ['off'] + ['...'] * 15))
        o2.append(add('a', arp_bar(ch, arp_octave, arp_rhythm)))
        o3.append(add('b', bass_bar(ch, style)))
    return {'format': 'worldfight65-music-1', 'name': title, 'tempo': tempo, 'volume': volume,
            'instruments': INSTRUMENTS, 'patterns': pats,
            'order': {'voice1': o1, 'voice2': o2, 'voice3': o3}, 'loop': intro_bars}


def title():
    # festive fanfare, C major: I - IV - V - I / vi - IV - V - V, twice with a variation
    a = [('C', [(0, 'G-4'), (2, 'C-5'), (6, 'E-5'), (8, 'G-5'), (12, 'E-5'), (14, 'C-5')]),
         ('F', [(0, 'A-5'), (4, 'G-5'), (6, 'F-5'), (8, 'A-5'), (12, 'off')]),
         ('G', [(0, 'G-5'), (2, 'F-5'), (4, 'E-5'), (6, 'D-5'), (8, 'B-4'), (10, 'D-5'), (14, 'off')]),
         ('C', [(0, 'C-5'), (8, 'off'), (10, 'G-4'), (12, 'C-5'), (14, 'D-5')]),
         ('Am', [(0, 'E-5'), (2, 'E-5'), (4, 'A-5'), (8, 'G-5'), (10, 'E-5'), (12, 'C-5')]),
         ('F', [(0, 'D-5'), (4, 'C-5'), (6, 'A-4'), (8, 'C-5'), (12, 'F-5')]),
         ('G', [(0, 'E-5'), (4, 'D-5'), (8, 'G-5'), (12, 'off'), (14, 'G-4')]),
         ('G', [(0, 'B-4'), (2, 'D-5'), (4, 'G-5'), (8, 'F-5'), (10, 'D-5'), (12, 'B-4')])]
    b = a[:4] + [('Am', [(0, 'A-5'), (4, 'G-5'), (6, 'E-5'), (8, 'C-6'), (12, 'B-5'), (14, 'A-5')]),
                 ('F', [(0, 'A-5'), (4, 'F-5'), (8, 'C-5'), (12, 'F-5')]),
                 ('G', [(0, 'G-5'), (2, 'A-5'), (4, 'B-5'), (8, 'D-6'), (12, 'B-5')]),
                 ('C', [(0, 'C-6'), (12, 'off')])]
    return piece('title', 'Campeonato (title)', 7, 12, a + b, 0, 'samba', 'brass', 4, [0, 3, 6, 10, 12])


def fight():
    # driving A minor: Am - F - G - Em ... bridge Dm - Am - E - E
    intro = [('Am', None), ('Am', None), ('F', None), ('G', [(8, 'E-4'), (10, 'G-4'), (12, 'A-4'), (14, 'B-4')])]
    a = [('Am', [(0, 'A-4'), (3, 'C-5'), (6, 'E-5'), (8, 'D-5'), (10, 'C-5'), (12, 'D-5'), (14, 'E-5')]),
         ('F', [(0, 'F-5'), (4, 'E-5'), (6, 'C-5'), (8, 'A-4'), (12, 'off')]),
         ('G', [(0, 'G-4'), (3, 'B-4'), (6, 'D-5'), (8, 'G-5'), (10, 'F-5'), (12, 'D-5'), (14, 'B-4')]),
         ('Em', [(0, 'E-5'), (8, 'off'), (10, 'E-5'), (12, 'G-5'), (14, 'B-5')])]
    a2 = a[:3] + [('Am', [(0, 'A-5'), (4, 'E-5'), (8, 'off'), (12, 'A-4'), (14, 'C-5')])]
    br = [('Dm', [(0, 'D-5'), (2, 'F-5'), (4, 'A-5'), (8, 'G-5'), (10, 'F-5'), (12, 'E-5')]),
          ('Am', [(0, 'C-5'), (4, 'E-5'), (8, 'A-5'), (12, 'off')]),
          ('Dm', [(0, 'F-5'), (2, 'E-5'), (4, 'D-5'), (8, 'A-4'), (12, 'D-5')]),
          ('E', [(0, 'E-5'), (2, 'G#5'), (4, 'B-5'), (8, 'G#5'), (12, 'E-5'), (14, 'D-5')])]
    br2 = br[:3] + [('E', [(0, 'B-4'), (4, 'D-5'), (8, 'E-5'), (12, 'G#4')])]
    return piece('fight', 'Copacabana Clash (fight)', 5, 12, intro + a + a2 + br + a + a2 + br2 + a + a2,
                 4, 'rock', 'lead', 3, [0, 2, 6, 8, 10, 14])


if __name__ == '__main__':
    for name, m in (('title', title()), ('fight', fight())):
        out = ROOT / 'music' / f'{name}.json'
        out.write_text(json.dumps(m, indent=1) + '\n')
        rows = sum(len(m['patterns'][p]) for p in m['order']['voice1'])
        print(f'{out}: {rows} rows, {rows * m["tempo"] / 50:.1f} s, {len(m["patterns"])} patterns')
