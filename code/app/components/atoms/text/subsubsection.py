from typing import Any, Dict, Optional

from components.atoms.atom import Atom
from constants import colors
from dash import html
from exceptions.ui import ComponentPropertyError


class SubSubsectionHeader(Atom):
    """Sub-subsection header component for Dash applications."""

    DEFAULT_STYLE = {
        "paddingTop": "1rem",
        "marginTop": "1rem",
    }

    TITLE_STYLE = {
        "color": colors.SECONDARY_COLOR,
        "fontSize": "1.0rem",
    }

    def __init__(
        self,
        title: str,
        style: Optional[Dict[str, Any]] = None,
    ):
        self._title = title
        self._style = {**self.DEFAULT_STYLE, **(style or {})}

        self.validate()

    def validate(self) -> None:
        """Validates the properties of the component."""
        if not self._title:
            raise ComponentPropertyError("Sub-subsection title cannot be empty. Please provide a valid title.")

    def render(self) -> html.Div:
        """Returns the HTML representation of the component."""
        return html.Div(
            children=[html.H4(self._title, style=self.TITLE_STYLE)],
            style=self._style,
        )
