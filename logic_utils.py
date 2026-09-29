import random


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    # FIX: Normal's range used to be 1-100 (wider than "Hard"'s), which made
    # Hard easier than Normal. Corrected to 1-50 so difficulty increases
    # in order: Easy (1-20) < Normal (1-50) < Hard (1-100).
    if difficulty == "Normal":
        return 1, 50
    # FIX: Hard's range used to be 1-50, same as (or narrower than) Normal.
    # Corrected to 1-100 so Hard is genuinely the widest/hardest range.
    if difficulty == "Hard":
        return 1, 100
    return 1, 50


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"

    Both guess and secret must be ints. A string secret (the old
    "convert secret to str on even attempts" glitch) is intentionally
    not supported here anymore and will raise TypeError.
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: hint messages were previously swapped with their outcome labels
    # (a guess that was too high told the player to go higher).
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    else:
        return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int, low: int, high: int):
    """Update score based on outcome and attempt number.

    A wrong guess ("Too High" or "Too Low") is penalized by a random amount
    scaled to the difficulty range, rather than a flat deduction, so harder
    difficulties (wider low/high ranges) sting more.
    """
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome in ("Too High", "Too Low"):
        penalty = random.randint(low // 2, high // 2)
        return current_score - penalty

    return current_score
