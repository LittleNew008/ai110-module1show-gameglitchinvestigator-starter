# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| before first guess| Attempts: 0 | Attempts: 1 | N/A |
| before first guess| Hard Difficualty range is 1-50 | Hard Difficulty range should be greater than Normal  | N/A|
| guess 24 when secret is 23| output go Lower| output go higher | go HIGHER! |
| normal guesses|History record each guess| missing most current guess| normal|
| start new game| Score reset to 0| Score preserved to last score| still shows game over.|
| second to last guess| one more guess| out of attempts and reveal secret| Out of attempts!|
|guess on the same higher or lower side as last guess| record attemp in history and subtract Attempts left| missing guess and attempt didn't get subtract| normal|

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

I used Claude Code (Claude Sonnet 5) as my AI teammate, asking it to trace `app.py`'s control flow before I changed anything rather than just describing the code.

**Correct suggestion:** I asked whether the `guess` argument to `check_guess()` (app.py:34) was guaranteed to be an int or could be a raw string, since I'm new to this codebase. Claude traced the call site back through `parse_guess()` and pointed out that `check_guess` is only ever called from the `else` branch after `parse_guess` returns `ok=True` (app.py:154-168), so `guess` is always an `int`. I verified this myself by re-reading that block and confirming there was no other call site.

**Suggestion I changed:** Once I understood `guess` was always an int, Claude flagged that `secret` was *not* guaranteed to be an int — it was being converted to a string on every even-numbered attempt (old app.py:162-166), with no real reason to do so. Claude's first framing implied I might also need to flip the `guess > secret` comparison in `check_guess`, since the FIXME comment there says the comparison is "intentionally reversed." I pushed back and asked it to check which side was actually wrong before touching the comparison operator itself. We determined the outcome labels (`Too High`/`Too Low`) were correct and only their paired hint messages (`Go HIGHER!`/`Go LOWER!`) were swapped, so instead of rewriting the comparison logic I had it swap just the messages — a smaller, easier-to-verify fix. I confirmed this against my bug log in section 1 (guess 24, secret 23 should say "Go LOWER!", not "Go HIGHER!").

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

I only counted a bug as fixed once I re-ran the exact repro steps from my section 1 bug log and confirmed the *actual* behavior now matched the *expected* behavior column — not just that the code looked different.

**Manual test:** With secret = 23 and guess = 24 (guess is higher than the secret), the app previously showed "📈 Go HIGHER!", which is backwards. After removing the secret-to-string conversion (old app.py:162-166) and swapping the hint messages in `check_guess` (app.py:34-41), I started a new game, used the "Developer Debug Info" expander to read the actual secret, and submitted guesses both above and below it across several attempts (both even- and odd-numbered) instead of just one guess. Every guess above the secret now returns "Too High" / "📉 Go LOWER!" and every guess below returns "Too Low" / "📈 Go HIGHER!", on every attempt number.

Claude helped me design this test: it pointed out the old bug depended on `st.session_state.attempts % 2`, so testing with a single guess wouldn't prove the fix — I needed guesses on both even and odd attempt counts to confirm the int/str type-alternation bug was actually gone, not just hidden by which attempt number I happened to test on.

**Automated test (pytest):** `tests/test_game_logic.py` imports `check_guess` from `logic_utils.py`, which was still a stub (`raise NotImplementedError`) — running `pytest tests/` before any of this showed all 3 starter tests failing on that, not on real assertions, so they weren't actually verifying anything yet. I implemented `check_guess` in `logic_utils.py` with the same fixed logic now in `app.py`, updated the 3 starter tests to unpack its `(outcome, message)` tuple, and added regression tests that pin the exact bug-log case (`check_guess(24, 23)` must return `"Too High"` and `"📉 Go LOWER!"`, not `"Go HIGHER!"`) plus one asserting `check_guess(24, "23")` now raises `TypeError` instead of silently falling back to a string comparison. Running `pytest tests/ -q` afterward showed `6 passed`, which is what convinced me the fix was real and not just "looked right" in the manual UI test.

**Manual test (bug 1, attempts counter):** The Developer Debug Info panel read "Attempts: 1" before I'd submitted a single guess, when it should read 0. The session-state initializer (app.py:93-96) already set `st.session_state.attempts = 0`, but nothing else in the file overwrote it before the first submit, so the off-by-one had to be stale session state carried over between edits/reruns rather than the initializer itself being wrong. I confirmed the fix by fully restarting the Streamlit server (not just clicking "New Game," which reuses the existing session) so `st.session_state` was rebuilt from scratch, then checked the debug panel before submitting anything: it now reads "Attempts: 0". I also relabeled the leftover `# FIXME` comment on that line to `# FIX` so it's clear the 0 is intentional and correct, not a leftover glitch.

**Manual test (bug, difficulty ranges):** "Hard" wasn't actually harder than "Normal." In `get_range_for_difficulty()` (app.py:4-13), "Normal" was returning a 1-100 range and "Hard" was returning 1-50 — so picking "Hard" gave you a *narrower*, easier range than "Normal." The values were already corrected to Normal = 1-50 and Hard = 1-100 in my working copy, but the old `# FIXME` comments above each branch still described the broken (pre-fix) values, which would've confused anyone reading the code. Selecting each difficulty in the sidebar one at a time and reading the "Range: X to Y" caption (app.py:92) confirmed it: Easy shows "Range: 1 to 20," Normal shows "Range: 1 to 50," and Hard shows "Range: 1 to 100" — a strictly increasing range size across the three levels, which is what "Hard" should mean. I then rewrote the stale comments to `# FIX` and described the actual before/after values so the reasoning is traceable from the code alone.

**Manual test (bug 4, history missing every other guess):** The history panel kept dropping guesses (bug log row 4: "missing most current guess"). Tracing `app.py` top to bottom turned up the real cause: the "Attempts left" banner and "Developer Debug Info" expander (old app.py:113-123) were rendered *before* the `if submit:` block (old app.py:151-191) that actually appends to `st.session_state.history` and increments `st.session_state.attempts`. Streamlit re-runs the whole script on every interaction, so whatever renders earlier in the file shows state from *before* the current run's mutation — the display was always one guess stale, and depending on how fast I clicked versus pressed Enter, that lag looked like alternating or missing entries. Moving the banner and expander to render *after* the submit block fixed it, so they read `st.session_state` post-mutation in the same run. To verify, I started a fresh game and submitted guesses 1, 2, 3, 4 in sequence: all four showed up in the History list and "Attempts left" decremented on every single submit, not every other one. I also had to swap out `st.stop()` (used once a game was already won or lost) for a `status == "playing"` guard on the submit block, since `st.stop()` halted the script before it ever reached the relocated display code — it would have hidden the debug panel entirely once a game ended.

**Manual test (bug 5, New Game not resetting state):** Starting a new game left things stale — the bug log flagged "still shows game over." Digging into the `new_game` handler (old app.py:126-130) showed why: it only reset `st.session_state.attempts` and `st.session_state.secret`, never `st.session_state.status` back to `"playing"` or `st.session_state.history` back to empty. So after winning or losing once, clicking "New Game 🔁" kept displaying "You already won. Start a new game to play again." indefinitely, and — worse — silently blocked all future guesses, since the submit block only runs `if st.session_state.status == "playing" and submit`. I also caught the new secret being drawn from a hardcoded `random.randint(1, 100)` instead of the selected difficulty's `low`/`high` range, so a new game under "Easy" could hand you a secret outside 1-20. Fixing all three in the same block — resetting `status` to `"playing"`, clearing `history` to `[]`, and using `random.randint(low, high)` — resolved it. To verify, I deliberately lost a game, clicked "New Game," and confirmed the stale message disappeared, the guess input accepted submissions again, and the History list in the debug panel came back empty; repeating the reset several times under "Easy" difficulty produced secrets only in the 1-20 range.

**Manual test (hint checkbox not redisplaying on re-enable):** Unchecking "Show hint" correctly hid the hint, but re-checking it did nothing until I submitted another guess — the last hint just stayed hidden. The cause was that `message` from `check_guess()` (old app.py:111-114) was a plain local variable, only computed and only ever passed to `st.warning()` inside the `if submit:` block. Clicking the checkbox triggers a rerun of its own, but `submit` evaluates to `False` on that rerun (it's not the button that was clicked), so the whole block — and the hint inside it — never runs; there was no stored value for a later rerun to redisplay. I fixed it by saving the message to `st.session_state.last_message` whenever a guess is processed (resetting it to `None` on new game and on a difficulty change, alongside the other per-game state), then rendering `st.warning(st.session_state.last_message)` outside the submit block, gated only on the checkbox's current value. To verify, I submitted a guess with the hint on, unchecked the box and watched the hint disappear, then rechecked it and confirmed the same hint reappeared immediately — no new guess required.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

I'd tell a friend that Streamlit has no event handlers or callbacks the way a typical UI framework does — there's no function that runs "when the button is clicked" while the rest of the app sits idle. Instead, clicking *any* widget (a button, a checkbox, even pressing Enter in a text box) makes Streamlit re-run your **entire script from the top**, and that widget's return value (like `st.button(...)`) just happens to be `True` for that one pass. Because local variables get wiped and recreated on every single rerun, anything that needs to survive between clicks — the secret number, the attempt count, the guess history — has to live in `st.session_state`, which is the one dict Streamlit keeps alive across reruns for that browser session.

The bugs I fixed this project all traced back to misunderstanding that model, just from different angles. Bug 4 happened because the code that *displayed* history was written earlier in the file than the code that *mutated* history — and since a rerun paints the page top-to-bottom in file order, the display always showed the previous run's state, one guess behind, not the state after processing this run's guess. Bug 5 happened because "New Game" only reset two of the four pieces of state that actually needed resetting (`attempts` and `secret`, but not `status` or `history`), so leftover state from the *previous* game silently carried into the new one and permanently blocked further guesses. The hint-checkbox bug was the same idea from a third angle: the hint text lived in a plain local variable instead of `st.session_state`, so it simply ceased to exist the moment a rerun happened for any reason other than clicking "Submit" — toggling the checkbox reruns the script too, just with `submit == False`, and a local variable has no memory of the previous run at all. The lesson I'd pass on: in Streamlit, always ask "in what order does this file execute on a rerun, which session_state values does this action need to touch, and does anything this widget shows depend on a variable that only gets set by a *different* widget's click?" — because there's no separate render phase, and no persistence outside `session_state`, to save you if you get either one wrong.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
