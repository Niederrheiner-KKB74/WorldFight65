#!/usr/bin/env python3
"""WorldFight65 music (Stage 6), composed by Claude as data: writes music/title.json and music/fight.json in
the format of docs/music_json.md (engine from ShooterMega65 Stage 19).

  python3 assets/source/compose_music.py

Each bar is one pattern of 16 rows (a row = a 16th note). Voice 1 melody, voice 2 arpeggio chords,
voice 3 bass and drums in turn (drums on the beats, bass between them).
- title: "Campeonato" - festive fanfare in C major with a samba-like syncopated bass, tempo 7 (~107 BPM),
  16 bars, loops from bar 1 (about 36 s).
- fight: "Samba da Briga" - samba in D minor, tempo 6 (125 BPM), 2 bars intro + 24 bars, loops after the
  intro (about 50 s); replaced "Copacabana Clash" after the owner's review (Stage 6).
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
    if name.endswith('m'):
        return 'arp_min'
    return 'arp_dom7' if name.endswith('7') else 'arp_maj'


def chord_root(name, octave):
    """'A#', 'Dm', 'E7', 'C' -> number of the root in this octave"""
    root = name[:2] if len(name) > 1 and name[1] == '#' else name[0] + '-'
    return note(root + str(octave))


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
    elif style == 'batucada':   # Stage 6 fight: surdo on 2 and 4, tamborim syncopation, partido-alto bass
        hits = {4: 'surdo', 12: 'surdo', 2: 'tamb', 7: 'tamb', 10: 'tamb', 15: 'tamb'}
        bass = {0: root, 3: root, 6: fifth, 8: root, 11: root + 12, 14: fifth}
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


def piece(name, title, tempo, volume, bars, intro_bars, style, lead, arp_octave, arp_rhythm, instruments=None):
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
            'instruments': instruments or INSTRUMENTS, 'patterns': pats,
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
    return piece('title', 'Campeonato (title)', 7, 10, a + b, 0, 'samba', 'brass', 4, [0, 3, 6, 10, 12])


# Stage 6, after the owner's review ("sounds like the shooter, should fit Brazil, quieter"): a samba in
# D minor - flute-like lead, cavaquinho strums in the partido-alto rhythm, surdo, tamborim and a walking
# samba bass - with its own instruments.
SAMBA = {
    'flute':    {'wave': 'triangle', 'attack': 1, 'decay': 6, 'sustain': 10, 'release': 5,
                 'vibrato': {'delay': 8, 'speed': 2, 'depth': 3}},
    'arp_min':  {'wave': 'pulse', 'attack': 0, 'decay': 4, 'sustain': 0, 'release': 2, 'pulse': 600,
                 'arpeggio': [0, 3, 7, 12]},
    'arp_maj':  {'wave': 'pulse', 'attack': 0, 'decay': 4, 'sustain': 0, 'release': 2, 'pulse': 600,
                 'arpeggio': [0, 4, 7, 12]},
    'arp_dom7': {'wave': 'pulse', 'attack': 0, 'decay': 4, 'sustain': 0, 'release': 2, 'pulse': 600,
                 'arpeggio': [0, 4, 7, 10]},
    'bass':     {'wave': 'triangle', 'attack': 0, 'decay': 6, 'sustain': 4, 'release': 2},
    'surdo':    {'attack': 0, 'decay': 9, 'sustain': 0, 'release': 0,
                 'wave_table': [['triangle', 'C-3'], ['triangle', 'G-2'], ['triangle', 'D-2'], ['triangle', 'A-1'],
                                ['triangle', 'F-1'], ['triangle', 'D-1']]},
    'tamb':     {'attack': 0, 'decay': 2, 'sustain': 0, 'release': 0,
                 'wave_table': [['pulse', 'E-6'], ['noise', 'C-7']]},
}


def fight():
    intro = [('Dm', None), ('A7', [(8, 'A-4'), (10, 'C#5'), (12, 'E-5'), (14, 'G-5')])]
    a = [('Dm', [(0, 'F-5'), (3, 'D-5'), (6, 'F-5'), (8, 'E-5'), (10, 'D-5'), (11, 'E-5'), (14, 'F-5')]),
         ('Dm', [(4, 'E-5'), (6, 'D-5'), (8, 'A-4'), (12, 'off')]),
         ('Gm', [(0, 'G-4'), (2, 'A#4'), (3, 'D-5'), (6, 'G-5'), (8, 'F-5'), (10, 'D-5'), (14, 'A#4')]),
         ('A7', [(2, 'A-4'), (4, 'C#5'), (6, 'E-5'), (8, 'G-5'), (11, 'F-5'), (12, 'E-5'), (14, 'C#5')]),
         ('Dm', [(0, 'D-5'), (3, 'F-5'), (6, 'A-5'), (8, 'G-5'), (10, 'F-5'), (12, 'E-5'), (14, 'D-5')]),
         ('A#', [(2, 'D-5'), (4, 'F-5'), (6, 'A#5'), (8, 'A-5'), (12, 'F-5')]),
         ('E7', [(0, 'E-5'), (2, 'G#5'), (4, 'B-5'), (6, 'D-6'), (8, 'B-5'), (10, 'G#5'), (12, 'E-5')]),
         ('A7', [(0, 'C#5'), (4, 'E-5'), (8, 'A-4'), (12, 'off')])]
    b = [('F', [(0, 'C-5'), (2, 'F-5'), (3, 'A-5'), (6, 'C-6'), (8, 'A-5'), (11, 'F-5'), (14, 'G-5')]),
         ('F', [(2, 'A-5'), (4, 'G-5'), (6, 'F-5'), (8, 'C-5'), (12, 'off')]),
         ('C7', [(0, 'E-5'), (3, 'G-5'), (6, 'A#5'), (8, 'A-5'), (10, 'G-5'), (12, 'E-5'), (14, 'C-5')]),
         ('C7', [(2, 'D-5'), (4, 'E-5'), (6, 'G-5'), (8, 'C-5'), (12, 'off')]),
         ('A#', [(0, 'D-5'), (2, 'F-5'), (3, 'A#5'), (6, 'D-6'), (8, 'C-6'), (10, 'A#5'), (12, 'A-5'), (14, 'G-5')]),
         ('Gm', [(0, 'F-5'), (4, 'D-5'), (6, 'A#4'), (8, 'G-4'), (12, 'A#4')]),
         ('A7', [(0, 'A-4'), (2, 'C#5'), (4, 'E-5'), (6, 'G-5'), (8, 'A-5'), (10, 'G-5'), (12, 'E-5'), (14, 'C#5')]),
         ('A7', [(0, 'A-4'), (4, 'off'), (8, 'E-4'), (10, 'G-4'), (12, 'A-4'), (14, 'C#5')])]
    return piece('fight', 'Samba da Briga (fight)', 6, 9, intro + a + b + a, 2, 'batucada', 'flute', 4,
                 [0, 2, 3, 5, 7, 9, 11, 12, 14], SAMBA)


if __name__ == '__main__':
    for name, m in (('title', title()), ('fight', fight())):
        out = ROOT / 'music' / f'{name}.json'
        out.write_text(json.dumps(m, indent=1) + '\n')
        rows = sum(len(m['patterns'][p]) for p in m['order']['voice1'])
        print(f'{out}: {rows} rows, {rows * m["tempo"] / 50:.1f} s, {len(m["patterns"])} patterns')
