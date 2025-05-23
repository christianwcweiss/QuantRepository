import pytest

from constants.colors import (
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    ACCENT_COLOR,
    BACKGROUND_COLOR,
    TEXT_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    ERROR_COLOR,
    get_text_color,
    LIGHT_TEXT_COLOR,
    DARK_TEXT_COLOR,
)


class TestColors:
    @pytest.mark.parametrize(
        "color, expected_text_color",
        [
            (PRIMARY_COLOR, LIGHT_TEXT_COLOR),
            (SECONDARY_COLOR, LIGHT_TEXT_COLOR),
            (ACCENT_COLOR, DARK_TEXT_COLOR),
            (BACKGROUND_COLOR, DARK_TEXT_COLOR),
            (TEXT_COLOR, LIGHT_TEXT_COLOR),
            (SUCCESS_COLOR, DARK_TEXT_COLOR),
            (WARNING_COLOR, DARK_TEXT_COLOR),
            (ERROR_COLOR, LIGHT_TEXT_COLOR),
        ],
    )
    def test_colors(self, color: str, expected_text_color: str) -> None:
        text_color = get_text_color(color)

        assert text_color == expected_text_color, f"Expected {expected_text_color} for {color}, but got {text_color}"
