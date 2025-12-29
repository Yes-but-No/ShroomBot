def int_to_ordinal(n: int) -> str:
    abs_n = abs(n)
    if 11 <= (abs_n % 100) <= 13:
        # Special case for numbers ending in 11, 12, or 13
        suffix = "th"
    else:
        # General case for other numbers
        last_digit = abs_n % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"

    return f"{n}{suffix}"
