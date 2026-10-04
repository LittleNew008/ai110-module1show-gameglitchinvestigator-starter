import pytest

from logic_utils import check_guess, get_range_for_difficulty, parse_guess, update_score


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"


# --- Regression tests for the reversed-hint-message fix ---
# Bug log (reflection.md, section 1): guess 24 / secret 23 showed
# "Go HIGHER!" when the guess was already above the secret. These pin the
# hint direction so that bug can't silently come back.


def test_guess_too_high_hints_go_lower():
    outcome, message = check_guess(24, 23)
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"


def test_guess_too_low_hints_go_higher():
    outcome, message = check_guess(23, 24)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


def test_guess_one_below_secret_hints_go_higher():
    # Boundary case: guess is the secret minus exactly 1.
    outcome, message = check_guess(22, 23)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


def test_guess_one_above_secret_hints_go_lower():
    # Boundary case: guess is the secret plus exactly 1.
    outcome, message = check_guess(24, 23)
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"


def test_check_guess_handles_negative_numbers():
    outcome, message = check_guess(-10, -5)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


def test_check_guess_handles_zero():
    outcome, _ = check_guess(0, 0)
    assert outcome == "Win"


# --- Regression test for the secret-to-string conversion fix ---
# app.py used to convert st.session_state.secret to a str on even attempts
# before calling check_guess, which forced a lexicographic string
# comparison instead of a numeric one. check_guess now assumes both
# arguments are always ints and no longer has a string-comparison fallback,
# so passing a string secret should fail loudly instead of silently
# comparing strings.


def test_check_guess_rejects_string_secret():
    with pytest.raises(TypeError):
        check_guess(24, "23")


def test_check_guess_rejects_string_guess():
    # Same glitch, mirrored: a string guess against an int secret must also
    # fail loudly instead of silently falling back to string comparison.
    with pytest.raises(TypeError):
        check_guess("24", 23)


# --- Tests for the Hard-should-be-harder-than-Normal range fix ---
# Bug log: Hard's range used to be 1-50, narrower than (or equal to)
# Normal's range, so Hard was not actually harder.


def test_easy_range():
    assert get_range_for_difficulty("Easy") == (1, 20)


def test_normal_range():
    assert get_range_for_difficulty("Normal") == (1, 50)


def test_hard_range():
    assert get_range_for_difficulty("Hard") == (1, 100)


def test_difficulty_ranges_increase_in_order():
    easy_low, easy_high = get_range_for_difficulty("Easy")
    normal_low, normal_high = get_range_for_difficulty("Normal")
    hard_low, hard_high = get_range_for_difficulty("Hard")
    assert easy_high < normal_high < hard_high


def test_unknown_difficulty_falls_back_to_a_default_range():
    # Unusual input: a difficulty string that doesn't match any branch.
    assert get_range_for_difficulty("Nightmare") == (1, 50)


def test_difficulty_lookup_is_case_sensitive():
    # "easy" (lowercase) doesn't match the "Easy" branch, so it should fall
    # back to the default range rather than silently matching Easy.
    assert get_range_for_difficulty("easy") == (1, 50)


def test_empty_string_difficulty_falls_back_to_default():
    assert get_range_for_difficulty("") == (1, 50)


# --- parse_guess: edge cases and unusual input ---


def test_parse_guess_plain_integer():
    assert parse_guess("42") == (True, 42, None)


def test_parse_guess_strips_surrounding_whitespace():
    assert parse_guess("  42  ") == (True, 42, None)


def test_parse_guess_accepts_explicit_plus_sign():
    assert parse_guess("+5") == (True, 5, None)


def test_parse_guess_accepts_negative_integer():
    assert parse_guess("-5") == (True, -5, None)


def test_parse_guess_truncates_positive_float_toward_zero():
    assert parse_guess("5.9") == (True, 5, None)


def test_parse_guess_truncates_negative_float_toward_zero():
    # int(float("-5.9")) == -5, not -6: truncates toward zero, not floor.
    assert parse_guess("-5.9") == (True, -5, None)


def test_parse_guess_leading_zeros():
    assert parse_guess("007") == (True, 7, None)


def test_parse_guess_rejects_empty_string():
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None
    assert err == "Enter a guess."


def test_parse_guess_rejects_none():
    ok, value, err = parse_guess(None)
    assert ok is False
    assert value is None
    assert err == "Enter a guess."


def test_parse_guess_rejects_whitespace_only_as_not_a_number():
    # Different from the empty-string case: whitespace isn't caught by the
    # `raw == ""` check, so it falls through to the int() parse and fails
    # with the "not a number" message instead of "Enter a guess."
    ok, value, err = parse_guess("   ")
    assert ok is False
    assert value is None
    assert err == "That is not a number."


def test_parse_guess_rejects_multiple_decimal_points():
    ok, value, err = parse_guess("4.5.6")
    assert ok is False
    assert err == "That is not a number."


def test_parse_guess_rejects_scientific_notation():
    # "1e3" has no "." so it's parsed with int(), which rejects it outright
    # even though it's a valid float -- documents current behavior.
    ok, value, err = parse_guess("1e3")
    assert ok is False
    assert err == "That is not a number."


def test_parse_guess_rejects_nan():
    ok, value, err = parse_guess("nan")
    assert ok is False
    assert err == "That is not a number."


def test_parse_guess_rejects_words():
    ok, value, err = parse_guess("banana")
    assert ok is False
    assert err == "That is not a number."


def test_parse_guess_rejects_comma_thousands_separator():
    ok, value, err = parse_guess("1,000")
    assert ok is False
    assert err == "That is not a number."


# --- update_score: win formula boundaries ---


def test_update_score_win_early_attempt_awards_more_points():
    # attempt_number=0 -> points = 100 - 10*(0+1) = 90
    assert update_score(0, "Win", attempt_number=0, low=1, high=20) == 90


def test_update_score_win_points_floor_is_clamped_to_ten():
    # attempt_number=8 -> raw points = 100 - 90 = 10 (the floor, unclamped)
    assert update_score(0, "Win", attempt_number=8, low=1, high=20) == 10


def test_update_score_win_beyond_floor_still_clamped_to_ten():
    # attempt_number=9 would go negative (100 - 100 = 0) without the clamp.
    assert update_score(0, "Win", attempt_number=9, low=1, high=20) == 10


def test_update_score_win_adds_to_existing_score():
    assert update_score(50, "Win", attempt_number=0, low=1, high=20) == 140


# --- update_score: scaled penalty for wrong guesses ---
# The penalty is random, scaled to the difficulty's range, so these tests
# pin the bounds rather than an exact value.


def test_update_score_too_high_penalty_is_within_range_bounds():
    low, high = 1, 20
    for _ in range(200):
        score = update_score(0, "Too High", attempt_number=1, low=low, high=high)
        penalty = -score
        assert low // 2 <= penalty <= high // 2


def test_update_score_too_low_penalty_is_within_range_bounds():
    low, high = 1, 100
    for _ in range(200):
        score = update_score(0, "Too Low", attempt_number=1, low=low, high=high)
        penalty = -score
        assert low // 2 <= penalty <= high // 2


def test_update_score_penalty_is_deterministic_with_seeded_random(monkeypatch):
    monkeypatch.setattr("logic_utils.random.randint", lambda a, b: 7)
    assert update_score(30, "Too High", attempt_number=1, low=1, high=20) == 23
    assert update_score(30, "Too Low", attempt_number=1, low=1, high=20) == 23


def test_update_score_unknown_outcome_leaves_score_unchanged():
    assert update_score(42, "Invalid", attempt_number=1, low=1, high=20) == 42


def test_update_score_unknown_outcome_preserves_negative_score():
    assert update_score(-5, "", attempt_number=1, low=1, high=20) == -5
