
import re
from datetime import date


def required_text(value, field_name):
    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} is required.")

    return value


def optional_text(value):
    value = value.strip()
    return value if value else None


def positive_integer(value, field_name):
    value = value.strip()

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be a whole number."
        ) from None

    if number <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return number


def valid_email(value):
    value = value.strip()

    if not value:
        return None

    # Basic format check for a desktop academic project.
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.fullmatch(pattern, value):
        raise ValueError("Enter a valid email address.")

    return value


def valid_phone(value):
    value = value.strip()

    if not value:
        return None

    # Accept an optional leading + and 7–15 digits.
    if not re.fullmatch(r"\+?[0-9]{7,15}", value):
        raise ValueError(
            "Phone must contain 7–15 digits, "
            "with an optional leading +."
        )

    return value


def valid_date_of_birth(value):
    value = value.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            "Date of birth must use YYYY-MM-DD format."
        ) from None

    if parsed_date > date.today():
        raise ValueError("Date of birth cannot be in the future.")

    return parsed_date
