import curses
from enum import Enum, auto
from prompt_toolkit.completion import Completer, Completion
from data import OpenQuestion, MultipleChoiceQuestion, ChallengeResult
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
    def __init__(self, user_name: str = "Player", battery_percentage: int = 100, distance_km: float = 0) -> None:
        option_config = MenuOptionConfig(
            width=20,
        )

        start_button = MenuOption("Takeoff", MainViewResult.TAKEOFF, option_config)
        inventory_button = MenuOption("Inventory", None, option_config)
        quit_button = MenuOption("Quit", MainViewResult.QUIT, option_config)
        self.buttons_menu = HorizontalMenu([BoxedElement(start_button), BoxedElement(inventory_button), BoxedElement(quit_button)], start_y=4)

        menu_width = self.buttons_menu.get_width()

        self.exit_menu = create_exit_window(start_y=4, start_x=menu_width // 2 // 2 - 4)
        self.show_exit_menu = False

        distance_prefix = "* "
        distance_suffix = " km"
        battery_prefix = "B "
        battery_suffix = " %"

        self.name_display = TextElement(user_name, width=menu_width, alignment=Alignment.LEFT)
        self.distance_display = TextElement(f"{distance_km}", prefix=distance_prefix, suffix=distance_suffix, width=menu_width, alignment=Alignment.CENTER)
        self.battery_display = TextElement(f"{battery_percentage}", prefix=battery_prefix, suffix=battery_suffix, width=menu_width, alignment=Alignment.RIGHT)

        elements: list[MenuElement] = [
            self.distance_display,
            self.battery_display,
        ]
        elements.extend(self.buttons_menu.menu_elements)
        super().__init__(elements)

    def set_distance(self, distance_km: float) -> None:
        self.distance_display.set_text(f"{distance_km:.1f}")

    def set_battery(self, battery: int) -> None:
        self.battery_display.set_text(f"{battery}")

    def get_width(self) -> int:
        return self.buttons_menu.get_width()

    def get_height(self) -> int:
        pass

    def on_draw(self, window: curses.window) -> None:
        x = 2
        y = 2

        self.name_display.draw(window, x, y)
        self.distance_display.draw(window, x, y)
        self.battery_display.draw(window, x, y)

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

        self.question_display = TextElement(mc_question.question, width=60, alignment=Alignment.CENTER)
        self.options_menu = HorizontalMenu([BoxedElement(MenuOption(opt.name, opt.name, option_config)) for opt in mc_question.options], start_y=4)
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
            window.clear()
            window.addstr(2, 2, "Correct!")
            window.addstr(4, 2, "Press any key to continue...")
            window.refresh()
            window.getch()
            return True
        elif result is not None:
            window.clear()
            window.addstr(2, 2, f"Wrong! The correct answer was: {self.correct_answer.name if self.correct_answer else 'N/A'}")
            window.addstr(4, 2, "Press any key to continue...")
            window.refresh()
            window.getch()
            return False
        return None
