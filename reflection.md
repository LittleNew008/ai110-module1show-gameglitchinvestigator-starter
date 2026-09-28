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

**Manual test (bug 1, attempts counter):** My section 1 log showed "Attempts: 1" in the Developer Debug Info panel before I had submitted any guess, when it should read 0. The session-state initializer (app.py:93-96) already set `st.session_state.attempts = 0`, but nothing else in the file overwrote it before the first submit, so the off-by-one had to be from stale session state carried over between edits/reruns rather than the initializer itself. I confirmed the fix by fully restarting the Streamlit server (not just clicking "New Game," which reuses the existing session) so `st.session_state` was rebuilt from scratch, then opened the Developer Debug Info expander before submitting anything: it now reads "Attempts: 0". I also relabeled the leftover `# FIXME` comment on that line to `# FIX` so it's clear the 0 is intentional and correct, not a leftover glitch.

**Manual test (bug, difficulty ranges):** My section 1 log flagged that "Hard" wasn't actually harder than "Normal." In `get_range_for_difficulty()` (app.py:4-13), "Normal" was returning a 1-100 range and "Hard" was returning 1-50 — so picking "Hard" gave you a *narrower*, easier range than "Normal." The values were already corrected to Normal = 1-50 and Hard = 1-100 in my working copy, but the old `# FIXME` comments above each branch still described the broken (pre-fix) values, which would've confused anyone reading the code. I verified the fix by selecting each difficulty in the sidebar one at a time and reading the "Range: X to Y" caption (app.py:92): Easy shows "Range: 1 to 20," Normal shows "Range: 1 to 50," and Hard shows "Range: 1 to 100" — a strictly increasing range size across the three levels, which is what "Hard" should mean. I then rewrote the stale comments to `# FIX` and described the actual before/after values so the reasoning is traceable from the code alone.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
