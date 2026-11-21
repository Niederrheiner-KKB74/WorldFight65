# Stage 8 – Second arena, balancing, polish

Test builds go to the owner as D81; the release goes to `releases/stage8/` when the stage is confirmed.

## What it does (test build 8a)
- **Zeche Zollverein, Essen** – Konrad's home arena from the owner's generator picture
  (`assets/art/arena/zollverein_source.png`, 1000 glyphs after merging one similar tile, 175 colours).
  Prompt: `docs/art_prompts_arena.md`.
- **Which arena:** the home arena of player 2's fighter (Tiago vs Konrad: Zollverein; Konrad vs Tiago: Rio).
  Mirror match: the arena changes with every match. The versus screen already shows the arena.
- **Balancing check:** CPU against CPU (`--define AUTOTEST --define AUTOTEST_CPUVS`, plus `AUTOTEST_SWAP`,
  `AUTOTEST_EASY` / `AUTOTEST_HARD`); the screen shows matches and rounds won per side.

  | Level | Tiago as player 1 | Konrad as player 1 | Total matches |
  |---|---|---|---|
  | normal | Tiago 6 : 4 | Tiago 6 : 3 | Tiago 12 : Konrad 7 |
  | hard | Konrad 5 : 0 | Konrad 10 : 0 | Konrad 15 : 0 |

  With Konrad's light attacks 1 weaker and his crouching jab/kick shortened from 49 to 42 or 45 px, hard
  flipped to Tiago 13 : 3 and 21 : 0. The hard CPU duel locks into a deterministic poke war that a few
  pixels decide; it does not say how balanced the game is between people. **No changes** - the values stay
  as confirmed by the owner. The tool stays for later fighters (`REACH_CAP` in a fighter module could
  shorten hit boxes measured on the art).

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): Zollverein on the versus screen and in the fight (mirror match); CPU, menus
  and title unchanged.
- Owner-confirmed on hardware: pending.

## Hardware checklist
1. Tiago (1P) against Konrad (2P/CPU): versus screen and fight at Zeche Zollverein.
2. Konrad (1P) against Tiago: Rio.
3. Mirror match: the arena changes with every match.
4. Zollverein picture: colours, the headframe, the cobblestones with the rails; fighters stand on the floor.
5. Back to the selection after a match, the next match in the right arena.
