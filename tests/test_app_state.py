"""
Integration tests for app.py's Streamlit session-state behavior, using
streamlit.testing.v1.AppTest. These cover bugs from reflection.md that live
in the UI/state-machine layer rather than in the pure logic_utils functions
(attempt counting, New Game reset, render ordering).
"""

from streamlit.testing.v1 import AppTest

GUESS_INPUT_KEY = "guess_input_Normal"  # Normal is the default sidebar selection
EASY_GUESS_INPUT_KEY = "guess_input_Easy"


def submit_guess(at: AppTest, guess: str, key: str = GUESS_INPUT_KEY) -> AppTest:
    at.text_input(key=key).set_value(guess)
    at.button[0].click()  # Submit Guess is the first button defined
    return at.run()


def click_new_game(at: AppTest) -> AppTest:
    at.button[1].click()  # New Game is the second button defined
    return at.run()


# --- Bug #1: attempts used to start at 1 instead of 0 ---


def test_attempts_start_at_zero_before_any_guess():
    at = AppTest.from_file("app.py").run()
    assert at.session_state["attempts"] == 0


def test_attempts_left_display_is_accurate_before_any_guess():
    at = AppTest.from_file("app.py").run()
    info_texts = [el.value for el in at.info]
    assert any("Attempts left: 8" in text for text in info_texts)  # Normal limit is 8


# --- Bug #4: history / debug panel was missing the most recent guess ---


def test_debug_panel_shows_guess_immediately_after_submit():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 50
    at = submit_guess(at, "10")

    assert at.session_state["history"] == [10]
    # The rendered debug panel (not just session_state) must reflect this
    # run's guess, not the previous run's -- this is what the render-order
    # bug actually broke.
    debug_json = at.expander[0].json[0].value
    assert debug_json == str([10])


def test_debug_panel_accumulates_history_across_multiple_guesses():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 999  # unreachable in range, guesses always wrong
    at = submit_guess(at, "10")
    at = submit_guess(at, "20")
    at = submit_guess(at, "30")

    assert at.session_state["history"] == [10, 20, 30]
    debug_json = at.expander[0].json[0].value
    assert debug_json == str([10, 20, 30])


def test_invalid_guess_is_still_recorded_in_history_immediately():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 50
    at = submit_guess(at, "not-a-number")

    assert at.session_state["history"] == ["not-a-number"]


# --- Bug #6: ran out of attempts one guess early (off-by-one) ---


def test_game_still_playing_one_guess_before_the_limit():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 1  # never matches a guess of 99
    for _ in range(7):  # Normal attempt_limit is 8
        at = submit_guess(at, "99")

    assert at.session_state["attempts"] == 7
    assert at.session_state["status"] == "playing"


def test_game_lost_exactly_at_the_limit():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 1
    for _ in range(8):
        at = submit_guess(at, "99")

    assert at.session_state["attempts"] == 8
    assert at.session_state["status"] == "lost"


def test_game_lost_boundary_differs_by_difficulty():
    # Easy has a tighter attempt_limit (6) -- make sure the off-by-one fix
    # holds for a limit other than Normal's.
    at = AppTest.from_file("app.py").run()
    at.sidebar.selectbox[0].set_value("Easy").run()
    at.session_state["secret"] = 1
    for _ in range(5):
        at = submit_guess(at, "99", key=EASY_GUESS_INPUT_KEY)
    assert at.session_state["status"] == "playing"

    at = submit_guess(at, "99", key=EASY_GUESS_INPUT_KEY)
    assert at.session_state["status"] == "lost"


def test_winning_on_the_last_possible_attempt_is_still_a_win():
    # Edge case combining the win path with the attempt-limit boundary.
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 50
    for _ in range(7):
        at = submit_guess(at, "1")  # guaranteed wrong, burns 7 attempts
    assert at.session_state["status"] == "playing"

    at = submit_guess(at, "50")  # 8th and final attempt: correct
    assert at.session_state["status"] == "won"


# --- Bug #5: New Game did not reset score, and (previously) left the old
# "Game Over" status in place.


def test_new_game_resets_status_away_from_game_over():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 1
    for _ in range(8):  # lose the game (Normal limit is 8)
        at = submit_guess(at, "99")
    assert at.session_state["status"] == "lost"

    at = click_new_game(at)
    assert at.session_state["status"] == "playing"


def test_new_game_resets_attempts_and_history():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 1
    at = submit_guess(at, "99")
    assert at.session_state["attempts"] == 1
    assert at.session_state["history"] == [99]

    at = click_new_game(at)
    assert at.session_state["attempts"] == 0
    assert at.session_state["history"] == []


def test_new_game_resets_score_to_zero():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 50
    at = submit_guess(at, "50")  # win, score becomes positive
    assert at.session_state["score"] > 0

    at = click_new_game(at)
    assert at.session_state["score"] == 0


# --- Difficulty switch mid-game (related state-reset path, same code shape
# as New Game) ---


def test_changing_difficulty_mid_game_resets_attempts_and_status():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 1
    for _ in range(8):
        at = submit_guess(at, "99")
    assert at.session_state["status"] == "lost"

    at.sidebar.selectbox[0].set_value("Hard")
    at = at.run()
    assert at.session_state["status"] == "playing"
    assert at.session_state["attempts"] == 0


def test_changing_difficulty_mid_game_resets_score():
    at = AppTest.from_file("app.py").run()
    at.session_state["secret"] = 50
    at = submit_guess(at, "50")
    assert at.session_state["score"] > 0

    at.sidebar.selectbox[0].set_value("Hard")
    at = at.run()
    assert at.session_state["score"] == 0
