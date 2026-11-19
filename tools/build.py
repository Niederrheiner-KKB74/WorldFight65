#!/usr/bin/env python3
"""Build WorldFight65: assemble with KickAssembler, write PRG + D81.

Usage:
  python3 tools/build.py [--kickass PATH] [--out DIR] [--define SYMBOL ...]

The KickAssembler jar (KickAss65CE02-5.25.jar) is not part of the repository.
It is looked up via --kickass, the KICKASS_JAR environment variable or
tools/bin/KickAss65CE02-5.25.jar, and its SHA-256 is checked.

Structure taken from ShooterMega65 Stage 19 (tools/build.py); asset generation
steps are added here as the stages need them.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import d81            # noqa: E402
import build_music    # noqa: E402

KICKASS_SHA256 = '5d8544280dae2d018c79151d8c7b877eca1fb994096e54ca380b26d0cd79f847'
PRG_NAME = 'WORLDFIGHT'
DISK_NAME = 'WORLDFIGHT65.D81'
DATA_FILES = ['A-RIO-GFX', 'A-RIO-MAP', 'T-TITLE-GFX', 'T-TITLE-MAP', 'F-TIAGO', 'F-KONRAD', 'MUSIC']   # SEQ files, loaded by src/main.asm


def find_kickass(arg):
    for cand in (arg, os.environ.get('KICKASS_JAR'), ROOT / 'tools/bin/KickAss65CE02-5.25.jar'):
        if cand and Path(cand).is_file():
            return Path(cand)
    sys.exit('KickAssembler not found: use --kickass or KICKASS_JAR (KickAss65CE02-5.25.jar)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kickass')
    ap.add_argument('--out', default=str(ROOT / 'build'))
    ap.add_argument('--allow-other-kickass', action='store_true')
    ap.add_argument('--define', action='append', default=[], help='test build: extra KickAssembler symbol')
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    jar = find_kickass(a.kickass)
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    if digest != KICKASS_SHA256 and not a.allow_other_kickass:
        sys.exit(f'unexpected KickAssembler build {digest}; pass --allow-other-kickass to continue')

    asset = subprocess.run([sys.executable, str(ROOT / 'tools/make_assets.py')], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(asset.stdout.strip())
    if asset.returncode:
        sys.exit('asset generation failed')
    try:
        print('\n'.join(build_music.main(ROOT / 'build/gen')))   # sound effects (Stage 5), music (Stage 6)
    except build_music.MusicError as e:
        sys.exit(f'music: {e}')
    chk = subprocess.run([sys.executable, str(ROOT / 'tools/check_assets.py')], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(chk.stdout.strip())
    if chk.returncode:
        sys.exit('asset check failed')

    prg = out / f'{PRG_NAME}.PRG'
    disk = out / DISK_NAME
    # A failed assembly must not leave a previous build looking current.
    prg.unlink(missing_ok=True)
    disk.unlink(missing_ok=True)
    defines = [x for d in a.define for x in ('-define', d)]
    run = subprocess.run(['java', '-jar', str(jar), str(ROOT / 'src/main.asm'), '-o', str(prg),
                          '-symbolfile', '-odir', str(out), '-showmem'] + defines,
                         cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = run.stdout
    (out / 'assembly.txt').write_text(log)
    if run.returncode or 'Error' in log:
        print(log)
        sys.exit('assembly failed')
    for line in log.splitlines():
        if line.startswith('  $') or 'Memory' in line:
            print(line)
    data = prg.read_bytes()
    if data[:2] != b'\x01\x20':
        sys.exit('PRG must load at $2001')
    if 0x2001 + len(data) - 2 > 0xC000:
        sys.exit('PRG must end below $C000')

    gen = ROOT / 'build/gen'
    files = [(PRG_NAME, data, d81.PRG)]
    for name in DATA_FILES:
        files.append((name, (gen / f'{name}.bin').read_bytes(), d81.SEQ))
    image = d81.build_disk(files)
    for fname, payload, _ in files:
        if d81.read_file(image, fname) != payload:
            sys.exit(f'D81 verification failed: {fname}')
    disk.write_bytes(image)
    print(f'{prg.name}: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()[:16]}')
    print(f'{disk.name}: verified (' + ', '.join(f'{n} {len(p)}' for n, p, _ in files) + ' bytes)')


if __name__ == '__main__':
    main()
