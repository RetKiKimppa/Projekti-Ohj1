import curses
from curses import textpad
from typing import overload, Any
from typing import Callable

from dataclasses import dataclass
from abc import ABC, abstractmethod

from enum import Enum, auto, Flag


class OptionStyleFlags(Flag):
    NONE = 0
    BOLD = auto()
    REVERSE = auto()
    COLOR = auto()
    SQUARE_BRACKETS = auto()


@dataclass
class Rect:
    y: int
    x: int
    width: int
    height: int


@overload
def draw_rectangle(window, x: int, y: int, width: int, height: int) -> None: ...


@overload
def draw_rectangle(window, rect: Rect) -> None: ...


def draw_rectangle(window, *args) -> None:
    if len(args) == 1 and isinstance(args[0], Rect):
        rect = args[0]
        box_left = rect.x
        box_top = rect.y
        box_right = rect.x + rect.width
        box_bottom = rect.y + rect.height
    elif len(args) == 4:
        x, y, width, height = args
        box_left = x
        box_top = y
        box_right = x + width
        box_bottom = y + height
    else:
        raise ValueError("Invalid arguments for draw_rectangle")
    textpad.rectangle(window, box_top, box_left, box_bottom, box_right)


class MenuElement(ABC):
    def __init__(self, width: int, height: int, is_selectable: bool):
        self.width = width
        self.height = height
        self.is_selectable = is_selectable

    def get_height(self) -> int:
        return self.height

    def get_width(self) -> int:
        return self.width

    def on_get_input(self, key: int) -> Any | None:
        return None

    @abstractmethod
    def draw(self, window: curses.window, x: int, y: int, highlighted: bool = False) -> None:
        pass

    def on_select(self, window: curses.window) -> Any | None:
        """Return Any to exit menu, None to continue"""
        return None


class BoxedElement(MenuElement):
    def __init__(self, element: MenuElement, horizontal_padding: int = 1, vertical_padding: int = 0):
        super().__init__(element.get_width() - 1 + horizontal_padding * 2,
                         element.get_height() + 1 + vertical_padding * 2, element.is_selectable)
        self.element = element
        self.horizontal_padding = horizontal_padding
        self.vertical_padding = vertical_padding

    def get_height(self) -> int:
        return self.element.get_height() + 2 + self.vertical_padding * 2

    def get_width(self) -> int:
        return self.element.get_width() - 1 + self.horizontal_padding * 2

    def draw(self, window: curses.window, x: int, y: int, highlighted: bool = False) -> None:
        horizontal_pad = self.horizontal_padding
        vertical_pad = self.vertical_padding
        self.element.draw(window, x + 1 + horizontal_pad, y + 1 + vertical_pad, highlighted)
        draw_rectangle(window, x, y, self.get_width(), self.get_height() - 1)

    def on_select(self, window: curses.window) -> Any | None:
        return self.element.on_select(window)

    def on_get_input(self, key: int) -> Any | None:
        return self.element.on_get_input(key)


class Alignment(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@dataclass
class MenuOptionConfig:
    width: int = -1
    height: int = -1
    style_flags: OptionStyleFlags = OptionStyleFlags.NONE
    highlight_flags: OptionStyleFlags = OptionStyleFlags.REVERSE
    dynamic_width: bool | None = None
    alignment: Alignment = Alignment.CENTER

    @staticmethod
    def default() -> "MenuOptionConfig":
        return MenuOptionConfig()


class MenuOption(MenuElement):
    def __init__(
            self,
            name: str,
            callback: Callable[[curses.window], Any | None] | Any | None,
            config: MenuOptionConfig = MenuOptionConfig.default(),
    ):
        super().__init__(
            config.width if config.width != -1 else len(name) + 2,
            config.height if config.height != -1 else 1,
            is_selectable=True,
        )
        self.name = name
        self.dynamic_text = name
        self.callback = callback
        self.style_flags = config.style_flags
        self.highlight_flags = config.highlight_flags
        self.dynamic_width = (config.dynamic_width if config.dynamic_width is not None else (config.width == -1))
        self.alignment = config.alignment

    def get_width(self) -> int:
        if self.dynamic_width:
            return len(self.dynamic_text) + 2
        else:
            return super().get_width()

    def draw(self, window: curses.window, x: int, y: int, highlighted: bool = False) -> None:
        self.dynamic_text = get_styled_text(self.name, self.style_flags if not highlighted else self.highlight_flags)
        if self.alignment == Alignment.CENTER:
            x += (self.get_width() - len(self.dynamic_text)) // 2 - 1
        elif self.alignment == Alignment.RIGHT:
            x += self.get_width() - len(self.dynamic_text) - 2
        flags = get_flags(self.style_flags if not highlighted else self.highlight_flags)
        max_y, max_x = window.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            safe_text = self.dynamic_text[:max_x - x]
            window.addstr(y, x, safe_text, flags)

    def on_select(self, window: curses.window) -> Any | None:
        if callable(self.callback):
            return self.callback(window)
        return self.callback


class TextElement(MenuElement):
    def __init__(self, text: str, width: int = -1, height: int = 1, prefix: str = "", suffix: str = "", style_flags: OptionStyleFlags = OptionStyleFlags.NONE, alignment: Alignment = Alignment.LEFT, offset_x: int = 0, offset_y: int = 0):
        self.prefix = prefix
        self.suffix = suffix
        self.full_text = prefix + text + suffix
        super().__init__(width if width != -1 else len(self.full_text) + 2, height, is_selectable=False)
        self.initial_width = width
        self.text = text
        self.style_flags = style_flags
        self.alignment = alignment
        self.offset_x = offset_x
        self.offset_y = offset_y

    def set_text(self, text: str, set_width: bool = False) -> None:
        self.text = text
        self.full_text = self.prefix + self.text + self.suffix
        if set_width:
            self.set_width(len(self.full_text) + 2)
        elif self.initial_width == -1:
            self.width = len(text)

    def set_prefix(self, prefix: str) -> None:
        self.prefix = prefix
        self.full_text = self.prefix + self.text + self.suffix
        if self.initial_width == -1:
            self.width = len(self.full_text)

    def set_suffix(self, suffix: str) -> None:
        self.suffix = suffix
        self.full_text = self.prefix + self.text + self.suffix
        if self.initial_width == -1:
            self.width = len(self.full_text)

    def get_width(self) -> int:
        if self.initial_width == -1:
            return len(self.full_text)
        else:
            return super().get_width()

    def set_width(self, width: int) -> None:
        self.initial_width = width
        self.width = width

    def draw(self, window: curses.window, x: int, y: int, highlighted: bool = False) -> None:
        x += self.offset_x
        y += self.offset_y
        display_text = get_styled_text(self.full_text, self.style_flags)
        if self.alignment == Alignment.CENTER:
            x += (self.get_width() - len(display_text)) // 2
        elif self.alignment == Alignment.RIGHT:
            x += self.get_width() - len(display_text)
        flags = get_flags(self.style_flags)

        max_y, max_x = window.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            # Truncate display_text to fit the window width
            safe_text = display_text[:max_x - x]
            window.addstr(y, x, safe_text, flags)


def get_styled_text(text: str, style_flags: OptionStyleFlags) -> str:
    if style_flags & OptionStyleFlags.SQUARE_BRACKETS:
        text = f"[{text}]"
    return text


def get_flags(style_flags: OptionStyleFlags) -> int:
    flags = 0
    if style_flags & OptionStyleFlags.BOLD:
        flags |= curses.A_BOLD
    if style_flags & OptionStyleFlags.REVERSE:
        flags |= curses.A_REVERSE
    if style_flags & OptionStyleFlags.COLOR:
        flags |= curses.color_pair(1)
    return flags


class InputHandler:
    def __init__(self):
        self.handlers = {}

    def register_handler(self, key: int, handler: Callable[[], Any | None] | Any | None) -> None:
        self.handlers[key] = handler

    def handle_input(self, key: int) -> Any | None:
        if key in self.handlers:
            if callable(self.handlers[key]):
                return self.handlers[key]()
            return self.handlers[key]
        return None


class Menu(ABC):
    def __init__(self, menu_elements: list[MenuElement], input_handler: InputHandler | None = None):
        self.menu_elements = menu_elements
        self.selectable_elements = [el for el in menu_elements if el.is_selectable]
        self.selected_index = 0
        self.input_handler = input_handler

    @abstractmethod
    def get_width(self) -> int:
        pass

    @abstractmethod
    def get_height(self) -> int:
        pass

    @abstractmethod
    def on_draw(self, window: curses.window) -> None:
        pass

    @abstractmethod
    def on_get_input(self, key: int, window: curses.window) -> Any | None:
        """Return True to exit menu, False to continue"""
        pass

    def add_element(self, element: MenuElement) -> None:
        self.menu_elements.append(element)
        if element.is_selectable:
            self.selectable_elements.append(element)

    def read_input(self, window: curses.window, key: int | None = None) -> Any | None:
        if key is None:
            key = window.getch()

        if self.input_handler is not None:
            result = self.input_handler.handle_input(key)
            if result is not None:
                return result

        for element in self.menu_elements:
            result = element.on_get_input(key)
            if result is not None:
                return result

        return self.on_get_input(key, window)



class HorizontalMenu(Menu):
    def __init__(self, menu_elements: list[MenuElement], spacing: int = 2, start_x: int = 2, start_y: int = 2, input_handler: InputHandler | None = None):
        super().__init__(menu_elements, input_handler)
        self.spacing = spacing
        self.start_y = start_y
        self.start_x = start_x
        self.additional_rows: list[tuple[list[MenuElement], int]] = []

    def get_width(self) -> int:
        total_width = sum(el.get_width() for el in self.menu_elements)
        total_spacing = self.spacing * (len(self.menu_elements) - 1) if len(self.menu_elements) > 1 else 0
        return total_width + total_spacing + self.start_x

    def get_height(self) -> int:
        max_height = max(el.get_height() for el in self.menu_elements) if self.menu_elements else 0
        return max_height + self.start_y

    def add_non_selectable(self, row: list[MenuElement], offset_y: int) -> None:
        self.additional_rows.append((row, offset_y))

    def on_draw(self, window) -> None:
        pos_x = self.start_x
        for idx, element in enumerate(self.menu_elements):
            selected = (element == self.selectable_elements[self.selected_index]) if element.is_selectable else False
            element.draw(window, pos_x, self.start_y, selected)
            pos_x += element.get_width() + self.spacing

        for row in self.additional_rows:
            pos_x = self.start_x
            for element in row[0]:
                element.draw(window, pos_x, self.start_y + row[1])
                pos_x += element.get_width() + self.spacing

    def on_get_input(self, key: int, window: curses.window) -> Any | None:
        if key == curses.KEY_LEFT and self.selected_index > 0:
            self.selected_index -= 1
        elif key == curses.KEY_RIGHT and self.selected_index < len(self.selectable_elements) - 1:
            self.selected_index += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return self.selectable_elements[self.selected_index].on_select(window)
        return None


class VerticalMenu(Menu):
    def __init__(self, menu_elements: list[MenuElement], spacing: int = 0, start_x: int = 2, start_y: int = 2):
        super().__init__(menu_elements)
        self.spacing = spacing
        self.start_y = start_y
        self.start_x = start_x

    def get_width(self) -> int:
        max_width = max(el.get_width() for el in self.menu_elements) if self.menu_elements else 0
        return max_width + self.start_x

    def get_height(self) -> int:
        total_height = sum(el.get_height() for el in self.menu_elements)
        total_spacing = self.spacing * (len(self.menu_elements) - 1) if len(self.menu_elements) > 1 else 0
        return total_height + total_spacing + self.start_y

    def on_draw(self, window):
        pos_y = self.start_y
        for idx, element in enumerate(self.menu_elements):
            selected = (element == self.selectable_elements[self.selected_index]) if element.is_selectable else False
            element.draw(window, self.start_x, pos_y, selected)
            pos_y += element.get_height() + self.spacing

    def on_get_input(self, key: int, window: curses.window) -> Any | None:
        if key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
        elif key == curses.KEY_DOWN and self.selected_index < len(self.selectable_elements) - 1:
            self.selected_index += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return self.selectable_elements[self.selected_index].on_select(window)
        return None


def _draw_menu_internal(window, layout: Menu, clear_on_refresh: bool) -> Any:
    curses.curs_set(0)

    while True:
        if clear_on_refresh:
            window.clear()
        layout.on_draw(window)
        result = layout.read_input(window)
        if result is not None:
            return result


def draw_menu(layout: Menu, clear_on_refresh: bool = True) -> Any:
    return curses.wrapper(lambda window: _draw_menu_internal(window, layout, clear_on_refresh))


def _draw_menu_horizontal(
        window,
        options: list[str],
        spacing: int,
        start_x: int,
        start_y: int,
        style_flags: OptionStyleFlags,
        highlight_flags: OptionStyleFlags) -> str:
    curses.curs_set(0)
    selected_index = 0
    y = start_y

    while True:
        window.clear()
        x = start_x
        for idx, text in enumerate(options):
            selected = (idx == selected_index)
            styled_text = get_styled_text(text, style_flags if not selected else highlight_flags)
            flags = get_flags(style_flags if not selected else highlight_flags)
            window.addstr(y, x, styled_text, flags)
            x += len(text) + spacing

        key = window.getch()
        if key == curses.KEY_LEFT and selected_index > 0:
            selected_index -= 1
        elif key == curses.KEY_RIGHT and selected_index < len(options) - 1:
            selected_index += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return options[selected_index]


def _draw_menu_vertical(
        window,
        options: list[str],
        spacing: int,
        start_x: int,
        start_y: int,
        style_flags: OptionStyleFlags,
        highlight_flags: OptionStyleFlags) -> str:
    curses.curs_set(0)
    selected_index = 0
    x = start_x

    while True:

        y = start_y
        for idx, option in enumerate(options):
            selected = (idx == selected_index)
            styled_text = get_styled_text(option, style_flags if not selected else highlight_flags)
            args = get_flags(style_flags if not selected else highlight_flags)
            window.addstr(y, x, styled_text, *args)
            y += 1 + spacing

        key = window.getch()
        if key == curses.KEY_UP and selected_index > 0:
            selected_index -= 1
        elif key == curses.KEY_DOWN and selected_index < len(options) - 1:
            selected_index += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return options[selected_index]


class MenuLayout(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


def simple_menu(
        options: list[str],
        layout: MenuLayout,
        spacing: int = -1,
        start_x: int = 2,
        start_y: int = 2,
        style_flags: OptionStyleFlags = OptionStyleFlags.NONE,
        highlight_flags: OptionStyleFlags = OptionStyleFlags.REVERSE) -> str:
    if layout == MenuLayout.HORIZONTAL:
        spacing = 2 if spacing == -1 else spacing
        return curses.wrapper(
            lambda window: _draw_menu_horizontal(window, options, spacing, start_x, start_y, style_flags,
                                                 highlight_flags))
    elif layout == MenuLayout.VERTICAL:
        spacing = 0 if spacing == -1 else spacing
        return curses.wrapper(
            lambda window: _draw_menu_vertical(window, options, spacing, start_x, start_y, style_flags,
                                               highlight_flags))
    else:
        raise ValueError("Invalid layout type")


#output = simple_menu(["Option 1", "Opt 2", "Option 3"], MenuLayout.HORIZONTAL)
#print("Selected:", output)

# config = MenuOptionConfig(
#     width=12,
#     highlight_flags=OptionStyleFlags.REVERSE,
#     alignment=Alignment.CENTER)
#
# element1 = MenuOption(
#     name="Option 1",
#     callback=lambda window: "Option 1",
#     config=config)
#
# element2 = MenuOption(
#     name="Option 2",
#     callback=lambda window: print("Option 2 selected"),
#     config=config)
#
# element3 = MenuOption(
#     name="Option 3",
#     callback=lambda window: print("Option 3 selected"),
#     config=config)
#
# textElement = TextElement("This is a text element", style_flags=OptionStyleFlags.BOLD | OptionStyleFlags.SQUARE_BRACKETS)
#
# drawer = HorizontalMenu([BoxedElement(element1), BoxedElement(element2), BoxedElement(element3), textElement], spacing=4)
# result = draw_menu(drawer)
# print("Menu exited with result:", result)