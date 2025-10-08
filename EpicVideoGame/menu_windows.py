import curses
from enum import Enum, auto
from prompt_toolkit.completion import Completer, Completion

from airport_util import CompassDirection
from data import OpenQuestion, MultipleChoiceQuestion, ChallengeResult, Difficulty
from menu_drawer import Menu, MenuElement, TextElement, MenuOption, Alignment, MenuOptionConfig, draw_menu, \
    HorizontalMenu, BoxedElement, InputHandler

country_names = ["USA", "Canada", "Mexico", "Brazil", "UK", "France", "Germany", "Italy", "Spain", "Russia", "China", "Japan", "India", "Australia", "South Africa"]

class AnyCompleter(Completer):
    def __init__(self, options: list[str]):
        super().__init__()
        self.options = options

    def get_completions(self, document, complete_event):
        text = document.text
        for option in self.options:
            if option.lower().startswith(text.lower()):
                yield Completion(option, start_position=-len(text))


class MainViewResult(Enum):
    TAKEOFF = auto()
    QUIT = auto()


def create_exit_window(start_y: int = 2, start_x: int = 2) -> HorizontalMenu:
    quit_button = MenuOption("Quit", True, MenuOptionConfig(width=20))
    resume_button = MenuOption("Resume", False, MenuOptionConfig(width=20))
    input_handler = InputHandler()
    input_handler.register_handler(8, False)  # ESC to resume
    return HorizontalMenu([BoxedElement(resume_button), BoxedElement(quit_button)], start_y=start_y, start_x=start_x, input_handler=input_handler)


class MainView(Menu):
    def __init__(self, user_name: str = "Player", battery_percentage: int = 100, distance_km: float = 0, current_country_name: str = "", current_airport_name: str = "", direction_to_goal: CompassDirection = CompassDirection.N, difficulty: Difficulty | None = None) -> None:
        option_config = MenuOptionConfig(
            width=20,
        )
        self.show_direction = True

        start_button = MenuOption("Takeoff", MainViewResult.TAKEOFF, option_config)
        statistics_button = MenuOption("Statistics", None, option_config)
        quit_button = MenuOption("Quit", MainViewResult.QUIT, option_config)
        self.buttons_menu = HorizontalMenu([BoxedElement(start_button), BoxedElement(statistics_button), BoxedElement(quit_button)], start_y=4)

        menu_width = self.buttons_menu.get_width()

        self.exit_menu = create_exit_window(start_y=4, start_x=menu_width // 2 // 2 - 4)
        self.show_exit_menu = False

        distance_prefix = "* "
        distance_suffix = " km"
        battery_prefix = "B "
        battery_suffix = " %"

        self.correct_continent_prefix = "✓ "
        self.correct_country_prefix = "✓ "

        # top row: name (left), distance (center), battery (right)
        self.name_display = TextElement(user_name, prefix="Pilot: ", width=menu_width, alignment=Alignment.LEFT)
        self.direction_display = TextElement(f"{direction_to_goal.value}", width=menu_width, alignment=Alignment.CENTER, offset_y=-1)
        self.distance_display = TextElement(f"{distance_km}", prefix=distance_prefix, suffix=distance_suffix, width=menu_width, alignment=Alignment.CENTER)
        self.battery_display = TextElement(f"{battery_percentage}", prefix=battery_prefix, suffix=battery_suffix, width=menu_width, alignment=Alignment.RIGHT)

        # bottom 2 rows: country (left), airport (left)
        self.continent_display = TextElement("N/A", alignment=Alignment.LEFT)
        self.country_display = TextElement(current_country_name, width=menu_width, alignment=Alignment.LEFT)
        self.airport_display = TextElement(current_airport_name, width=menu_width, alignment=Alignment.LEFT)
        self.difficulty_display = TextElement(difficulty.value if difficulty else "N/A", width=menu_width, alignment=Alignment.RIGHT)

        elements: list[MenuElement] = [
            self.distance_display,
            self.battery_display,
            self.name_display,
            self.country_display,
            self.airport_display,
        ]
        elements.extend(self.buttons_menu.menu_elements)
        super().__init__(elements)

    def set_direction(self, direction: CompassDirection) -> None:
        self.direction_display.set_text(f"{direction.value}")

    def set_distance(self, distance_km: float) -> None:
        self.distance_display.set_text(f"{distance_km:.1f}")

    def set_battery(self, battery: int) -> None:
        self.battery_display.set_text(f"{battery}")

    def set_continent(self, continent_name: str) -> None:
        self.continent_display.set_text(continent_name)

    def set_country(self, country_name: str) -> None:
        self.country_display.set_text(country_name)

    def set_airport(self, airport_name: str) -> None:
        self.airport_display.set_text(airport_name)

    def set_difficulty(self, difficulty: Difficulty) -> None:
        self.difficulty_display.set_text(difficulty.value.capitalize())

    def show_correct_continent(self, show: bool = True) -> None:
        if show:
            self.continent_display.set_prefix(self.correct_continent_prefix)
        else:
            self.continent_display.set_prefix("")

    def show_correct_country(self, show: bool = True) -> None:
        if show:
            self.country_display.set_prefix(self.correct_country_prefix)
        else:
            self.country_display.set_prefix("")

    def get_width(self) -> int:
        return self.buttons_menu.get_width()

    def get_height(self) -> int:
        pass

    def on_draw(self, window: curses.window) -> None:
        x = 2
        y = 2

        self.name_display.draw(window, x, y)
        if self.show_direction:
            self.direction_display.draw(window, x, y)
        self.distance_display.draw(window, x, y)
        self.battery_display.draw(window, x, y)

        self.continent_display.draw(window, x, y + 6)
        self.country_display.draw(window, x + self.continent_display.get_width() + 2, y + 6)
        self.airport_display.draw(window, x, y + 7)

        self.difficulty_display.draw(window, x, y + 6)

        if self.show_exit_menu:
            self.exit_menu.on_draw(window)
        else:
            self.buttons_menu.on_draw(window)

    def on_get_input(self, key: int, window: curses.window) -> MainViewResult | None:
        """Return True to exit menu, False to continue"""
        if key in(8, curses.KEY_BACKSPACE) and not self.show_exit_menu:  # Backspace
            self.show_exit_menu = True
            self.exit_menu.on_draw(window)
            return None

        if self.show_exit_menu:
            exit_result = self.exit_menu.read_input(window, key=key)
            if exit_result is False:
                self.show_exit_menu = False
                return None
            elif exit_result is True:
                return MainViewResult.QUIT

        result = self.buttons_menu.on_get_input(key, window)

        if result is MainViewResult.QUIT:
            self.show_exit_menu = True
            self.exit_menu.on_draw(window)
            return None
        else:
            return result


class MultipleChoiceWindow(Menu):
    def __init__(self, mc_question: MultipleChoiceQuestion) -> None:
        option_config = MenuOptionConfig(
            width=20,
        )
        self.options = mc_question.options
        self.correct_answer = next((opt for opt in mc_question.options if opt.is_correct), None)

        self.options_menu = HorizontalMenu([BoxedElement(MenuOption(opt.name, opt.name, option_config)) for opt in mc_question.options], start_y=4)
        self.question_display = TextElement(mc_question.question, width=self.options_menu.get_width(), alignment=Alignment.CENTER)
        elements: list[MenuElement] = [
            self.question_display,
        ]
        elements.extend(self.options_menu.menu_elements)
        super().__init__(elements)

    def get_width(self) -> int:
        return self.options_menu.get_width()

    def get_height(self) -> int:
        return self.options_menu.get_height() + 4

    def on_draw(self, window: curses.window) -> None:
        x = 2
        y = 2

        self.question_display.draw(window, x, y)
        self.options_menu.on_draw(window)

    def on_get_input(self, key: int, window: curses.window) -> bool | None:
        result = self.options_menu.on_get_input(key, window)
        if result is not None and result == self.correct_answer.name:
            return True
        elif result is not None:
            return False
        return None

class TextWindow(Menu):
    def __init__(self, elements: list[TextElement], start_x: int = 2, start_y: int = 2, autosize_to_highest_width: bool = True) -> None:
        self.start_x = start_x
        self.start_y = start_y
        if autosize_to_highest_width:
            max_width = max(element.get_width() for element in elements)
            for element in elements:
                element.set_width(max_width)
        super().__init__(elements)

    def get_width(self) -> int:
        return max(element.get_width() for element in self.menu_elements) + self.start_x * 2

    def get_height(self) -> int:
        return sum(element.get_height() for element in self.menu_elements) + self.start_y * 2

    def on_draw(self, window: curses.window) -> None:
        x = 2
        y = 2

        for i, element in enumerate(self.menu_elements):
            element.draw(window, x, y)
            y += element.get_height()

    def on_get_input(self, key: int, window: curses.window) -> bool | None:
        return True