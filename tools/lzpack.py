#!/usr/bin/env python3
"""WorldFight65 data compression (Stage 10): an LZ4-like byte format that the 45GS02 unpacks quickly
(src/unpack.asm), used for the fighter packages and the picture glyphs. The game loads a packed file into
attic RAM and unpacks it once while the title is shown; at run time nothing changes.

Format "WZ":
  'W' 'Z' size(3 bytes, little endian, unpacked)
  sequences:  token = literals(4 bits) << 4 | (match length - 4)(4 bits)
              [literal count extension: bytes of 255 ..., then one byte < 255]   (when literals = 15)
              literals
              offset (2 bytes, little endian; 0 = end of data, the match part is then absent)
              [match length extension as above]                                  (when match nibble = 15)
A match copies `length` bytes from `offset` bytes back in the output (may overlap, byte by byte forward).

  python3 tools/lzpack.py IN OUT      # packs and checks the round trip
"""
import sys
from collections import defaultdict
from pathlib import Path

MIN_MATCH = 4
WINDOW = 65535
CHAIN = 96          # match candidates looked at per position


def _ext(out, v):
    while v >= 255:
        out.append(255)
        v -= 255
    out.append(v)


def _emit(out, lits, off, mlen):
    ln = len(lits)
    m = 0 if off == 0 else mlen - MIN_MATCH
    out.append((min(ln, 15) << 4) | min(m, 15))
    if ln >= 15:
        _ext(out, ln - 15)
    out += lits
    out += bytes((off & 0xff, off >> 8))
    if off and m >= 15:
        _ext(out, m - 15)


def _longest(b, i, heads):
    n = len(b)
    best, bo = 0, 0
    cands = heads.get(b[i:i + MIN_MATCH])
    if not cands:
        return 0, 0
    for p in reversed(cands[-CHAIN:]):
        if i - p > WINDOW:
            break
        if best and (i + best >= n or b[p + best] != b[i + best]):
            continue                    # cannot be longer than the best one so far
        ln = 0
        while i + ln < n and b[p + ln] == b[i + ln]:
            ln += 1
        if ln > best:
            best, bo = ln, i - p
    return best, bo


def pack(data):
    b = bytes(data)
    n = len(b)
    out = bytearray(b'WZ' + n.to_bytes(3, 'little'))
    heads = defaultdict(list)
    lits = bytearray()
    i = 0

    def add(k):
        if k + MIN_MATCH <= n:
            heads[b[k:k + MIN_MATCH]].append(k)
    while i < n:
        ln, off = _longest(b, i, heads) if i + MIN_MATCH <= n else (0, 0)
        if ln >= MIN_MATCH and i + 1 + MIN_MATCH <= n:      # lazy matching: a longer match one byte later?
            add(i)
            ln2, off2 = _longest(b, i + 1, heads)
            if ln2 > ln + 1:
                lits.append(b[i])
                i += 1
                ln, off = ln2, off2
            else:
                heads[b[i:i + MIN_MATCH]].pop()
        if ln >= MIN_MATCH:
            _emit(out, lits, off, ln)
            lits = bytearray()
            for k in range(i, i + ln):
                add(k)
            i += ln
        else:
            lits.append(b[i])
            add(i)
            i += 1
    _emit(out, lits, 0, 0)
    return bytes(out)


def unpack(p):
    assert p[:2] == b'WZ'
    size = int.from_bytes(p[2:5], 'little')
    out = bytearray()
    i = 5
    while True:
        tok = p[i]
        i += 1
        ln = tok >> 4
        if ln == 15:
            while True:
                v = p[i]
                i += 1
                ln += v
                if v != 255:
                    break
        out += p[i:i + ln]
        i += ln
        off = p[i] | p[i + 1] << 8
        i += 2
        if off == 0:
            break
        m = tok & 15
        if m == 15:
            while True:
                v = p[i]
                i += 1
                m += v
                if v != 255:
                    break
        m += MIN_MATCH
        s = len(out) - off
        for k in range(m):
            out.append(out[s + k])
    assert len(out) == size, (len(out), size)
    return bytes(out)


def pack_checked(data):
    p = pack(data)
    if unpack(p) != bytes(data):
        raise SystemExit('lzpack: round trip failed')
    return p


if __name__ == '__main__':
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    d = src.read_bytes()
    p = pack_checked(d)
    dst.write_bytes(p)
    print(f'{src.name}: {len(d)} -> {len(p)} bytes ({len(p) / len(d):.0%})')
