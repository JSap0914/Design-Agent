"""
ASCII UI generation engine for Design Agent.

Creates pixel-perfect ASCII mockups following strict format requirements:
- Mobile screens: EXACTLY 40 characters wide
- Web screens: EXACTLY 80 characters wide
- Box drawing characters: ┌─┐│└┘
- Buttons: [Text]
- Input fields: [_____]
- Icons: emoji (📱 🔍 👤 ⚙️)
"""

from typing import Literal

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ASCIIUIGenerator:
    """
    ASCII UI generation engine.

    Generates pixel-perfect ASCII mockups for mobile and web platforms.
    """

    # Box drawing characters
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    HORIZONTAL = "─"
    VERTICAL = "│"

    def __init__(self, platform: Literal["mobile", "web"] = "mobile"):
        """
        Initialize ASCII UI generator.

        Args:
            platform: "mobile" (40 chars) or "web" (80 chars)
        """
        self.platform = platform
        self.width = (
            settings.ascii_ui_width_mobile
            if platform == "mobile"
            else settings.ascii_ui_width_web
        )
        logger.info(f"ASCII UI generator initialized for {platform} ({self.width} chars wide)")

    def validate_width(self, line: str) -> bool:
        """
        Validate that a line is exactly the correct width.

        Args:
            line: Line to validate

        Returns:
            True if line is exactly self.width characters
        """
        return len(line) == self.width

    def pad_line(self, content: str, align: Literal["left", "center", "right"] = "left") -> str:
        """
        Pad content to exact width with spaces.

        Args:
            content: Content to pad
            align: Alignment ("left", "center", "right")

        Returns:
            Padded line of exact width
        """
        # Account for vertical borders (2 chars: │...│)
        inner_width = self.width - 2
        content_len = len(content)

        if content_len > inner_width:
            # Truncate if too long
            content = content[:inner_width]
            content_len = inner_width

        # Calculate padding
        padding_needed = inner_width - content_len

        if align == "center":
            left_pad = padding_needed // 2
            right_pad = padding_needed - left_pad
            padded = " " * left_pad + content + " " * right_pad
        elif align == "right":
            padded = " " * padding_needed + content
        else:  # left
            padded = content + " " * padding_needed

        return f"{self.VERTICAL}{padded}{self.VERTICAL}"

    def create_header(self) -> str:
        """
        Create top border line.

        Returns:
            Top border: ┌──────...──────┐
        """
        return f"{self.TOP_LEFT}{self.HORIZONTAL * (self.width - 2)}{self.TOP_RIGHT}"

    def create_footer(self) -> str:
        """
        Create bottom border line.

        Returns:
            Bottom border: └──────...──────┘
        """
        return f"{self.BOTTOM_LEFT}{self.HORIZONTAL * (self.width - 2)}{self.BOTTOM_RIGHT}"

    def create_divider(self) -> str:
        """
        Create horizontal divider line.

        Returns:
            Divider: ├──────...──────┤
        """
        return f"├{self.HORIZONTAL * (self.width - 2)}┤"

    def create_empty_line(self) -> str:
        """
        Create empty line with borders.

        Returns:
            Empty line: │      ...      │
        """
        return self.pad_line("")

    def create_button(self, text: str, align: Literal["left", "center", "right"] = "center") -> str:
        """
        Create button line.

        Args:
            text: Button text
            align: Button alignment

        Returns:
            Line with button: │    [Button Text]    │
        """
        button = f"[{text}]"
        # Add some padding around button
        button_with_padding = f"  {button}  "
        return self.pad_line(button_with_padding, align=align)

    def create_input(
        self, label: str, width: int = 20, align: Literal["left", "center"] = "left"
    ) -> list[str]:
        """
        Create input field (label + input box).

        Args:
            label: Input label
            width: Input box width
            align: Alignment

        Returns:
            List of lines: [label line, input line]
        """
        label_line = self.pad_line(f"  {label}", align=align)
        input_box = f"[{'_' * width}]"
        input_line = self.pad_line(f"  {input_box}", align=align)
        return [label_line, input_line]

    def create_text_line(
        self, text: str, align: Literal["left", "center", "right"] = "left", icon: str = ""
    ) -> str:
        """
        Create text line with optional icon.

        Args:
            text: Text content
            align: Text alignment
            icon: Optional emoji icon

        Returns:
            Text line with borders
        """
        if icon:
            content = f"  {icon} {text}"
        else:
            content = f"  {text}"

        return self.pad_line(content, align=align)

    def validate_ascii_ui(self, ascii_ui: str) -> tuple[bool, list[str]]:
        """
        Validate ASCII UI mockup.

        Checks:
        - All lines are exactly the correct width
        - Has top and bottom borders
        - Uses correct box drawing characters

        Args:
            ascii_ui: ASCII UI mockup to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        lines = ascii_ui.split("\n")
        errors = []

        # Check if empty
        if not lines:
            errors.append("ASCII UI is empty")
            return False, errors

        # Check top border
        if not lines[0].startswith(self.TOP_LEFT):
            errors.append("Top border missing or incorrect")

        # Check bottom border
        if not lines[-1].startswith(self.BOTTOM_LEFT):
            errors.append("Bottom border missing or incorrect")

        # Check all line widths
        for i, line in enumerate(lines):
            if len(line) != self.width:
                errors.append(
                    f"Line {i+1} has {len(line)} chars (expected {self.width}): '{line}'"
                )

        is_valid = len(errors) == 0
        return is_valid, errors


# Utility functions for quick mockup creation
def create_simple_mobile_mockup(
    title: str, elements: list[dict], navigation: str = "☰"
) -> str:
    """
    Create a simple mobile mockup (40 chars wide).

    Args:
        title: Screen title
        elements: List of UI elements (type, content)
        navigation: Navigation icon (default: hamburger menu)

    Returns:
        ASCII UI mockup

    Example:
        elements = [
            {"type": "text", "content": "Welcome!"},
            {"type": "input", "label": "Email", "width": 20},
            {"type": "button", "text": "Sign In"},
        ]
    """
    generator = ASCIIUIGenerator(platform="mobile")
    lines = []

    # Header
    lines.append(generator.create_header())

    # Title bar
    title_content = f"  📱 {title}"
    title_line = generator.pad_line(title_content, align="left")
    # Add navigation icon at end
    title_line = title_line[:-3] + f"{navigation}  {generator.VERTICAL}"
    lines.append(title_line)

    lines.append(generator.create_divider())

    # Content
    for element in elements:
        lines.append(generator.create_empty_line())

        if element["type"] == "text":
            lines.append(
                generator.create_text_line(
                    element["content"],
                    align=element.get("align", "left"),
                    icon=element.get("icon", ""),
                )
            )

        elif element["type"] == "input":
            input_lines = generator.create_input(
                element["label"], width=element.get("width", 20), align=element.get("align", "left")
            )
            lines.extend(input_lines)

        elif element["type"] == "button":
            lines.append(
                generator.create_button(element["text"], align=element.get("align", "center"))
            )

        elif element["type"] == "divider":
            lines.append(generator.create_divider())

        elif element["type"] == "empty":
            pass  # Already added above

    # Footer
    lines.append(generator.create_empty_line())
    lines.append(generator.create_footer())

    return "\n".join(lines)


# Export for easy import
__all__ = ["ASCIIUIGenerator", "create_simple_mobile_mockup"]
