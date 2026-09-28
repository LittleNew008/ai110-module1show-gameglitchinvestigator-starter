import pytest

from logic_utils import check_guess

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
