# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

**Purpose:** Glitchy Guesser is a Streamlit number-guessing game. Pick a difficulty, the app picks a secret number in that difficulty's range, and you guess it within a limited number of attempts, getting "higher/lower" hints and a score after each guess. The starter version was intentionally broken so the challenge was to find and fix the glitches, then back the fixes with tests.

**Bugs found** (full repro steps and console output are logged in [reflection.md](reflection.md), section 1):

1. **Off-by-one attempts counter** — the debug panel read "Attempts: 1" before any guess was submitted.
2. **Hard mode easier than Normal mode** — `get_range_for_difficulty()` had Normal returning 1–100 and Hard returning 1–50, the opposite of what the labels implied.
3. **Reversed hints** — guessing above the secret returned "Go HIGHER!" instead of "Go LOWER!" (the outcome label was correct; only the paired hint message was swapped).
4. **History dropping every other guess** — the "Attempts left" banner and debug panel were rendered *before* the code that mutates `st.session_state.history`/`attempts`, so the display always lagged one guess behind on Streamlit's rerun model.
5. **"New Game" not resetting state** — only `attempts` and `secret` were reset, so `status` and `history` carried over, locking out all further guesses after a win/loss and leaving a stale "Game Over" message.
6. **Hint checkbox not redisplaying** — the hint text lived in a local variable instead of `st.session_state`, so re-checking "Show hint" after unchecking it did nothing until another guess was submitted.
7. **Secret vs. guess type mismatch** — `secret` was converted to a string on every even-numbered attempt, forcing `check_guess` into a lexicographic string comparison half the time.

**Fixes applied:**

- Initialized `st.session_state.attempts` to `0` instead of `1`.
- Corrected the Normal/Hard ranges (and their stale comments) so difficulty strictly increases in range size.
- Swapped the hint messages (not the comparison logic) so they match the already-correct outcome labels.
- Moved the "Attempts left" banner and debug expander to render *after* the submit block, and replaced an `st.stop()` call with a `status == "playing"` guard so post-game state still renders.
- Reset `status`, `history`, and (after a later test caught it — see below) `score` back to their initial values in both the "New Game" handler and the difficulty-change branch, and drew the new secret from the selected difficulty's range instead of a hardcoded `1–100`.
- Moved the last hint message into `st.session_state.last_message` and rendered it from there, gated only on the checkbox's current value.
- Removed the secret-to-string conversion so `check_guess` always compares two ints.
- Moved all of this logic into `logic_utils.py` (`check_guess`, `get_range_for_difficulty`, `parse_guess`, `update_score`) so it's unit-testable outside of Streamlit.

See [reflection.md](reflection.md) for the full bug log, how AI was used to find and verify each fix, and what I'd do differently next time.

## 📸 Demo Walkthrough

1. Run `python -m streamlit run app.py` and open the app in the browser.
2. In the sidebar, pick a difficulty — Easy (1–20, 6 attempts), Normal (1–50, 8 attempts), or Hard (1–100, 5 attempts). The sidebar caption shows the active range and attempt limit.
3. Expand "Developer Debug Info" to see the secret number, current attempt count (starts at 0), score, and guess history.
4. Type a guess and click "Submit Guess 🚀". The app reports "Too High"/"Too Low" with a matching hint ("📉 Go LOWER!" or "📈 Go HIGHER!"), updates the score, appends the guess to History, and decrements "Attempts left" — every time, not just every other guess.
5. Uncheck and re-check "Show hint" to confirm the last hint reappears immediately without needing another guess.
6. Keep guessing until you win (confetti + final score) or run out of attempts (reveal of the secret). The status message persists correctly instead of getting stuck.
7. Click "New Game 🔁" — attempts, score, history, and status all reset, and a new secret is drawn from the current difficulty's range.
8. Switch difficulty mid-game to confirm it also starts a fresh game in the new range instead of keeping a secret that could fall outside it.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
pytest tests/ -q
........................................................                 [100%]
56 passed in 1.77s
```

`tests/test_game_logic.py` (42 tests) covers the pure logic in `logic_utils.py` — `check_guess`, `get_range_for_difficulty`, `parse_guess`, and `update_score`, including boundary cases and the string-vs-int `TypeError` regression. `tests/test_app_state.py` (14 tests) uses `streamlit.testing.v1.AppTest` to drive `app.py` as a simulated session and assert on `session_state` directly — this is what caught the score not resetting on "New Game."

## 🚀 Stretch Features

- [x] **Difficulty-based ranges and attempt limits** — Easy/Normal/Hard each map to a distinct number range (1–20 / 1–50 / 1–100) and attempt limit (6 / 8 / 5), with the sidebar showing both for the selected difficulty.
- [x] **Scoring system** — `update_score()` awards points on a win based on how many attempts were used (fewer attempts, higher score) and applies a small randomized penalty on a miss, surfaced live in the debug panel.
- [x] **Guess history** — every submitted guess (valid or invalid input) is appended to `st.session_state.history` and shown in the debug panel.
- [x] **Persistent hint toggle** — "Show hint" can be unchecked and re-checked at any time without needing to resubmit a guess to see the hint again.
