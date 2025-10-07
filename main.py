from enum import Enum, auto

import game
from prompt_utils import safe_prompt
from game import Difficulty, OpenQuestion, MultipleChoiceQuestion
from prompt_toolkit.completion import Completer, Completion
from menu_drawer import draw_menu, VerticalMenu
from menu_windows import MainView, MainViewResult, MultipleChoiceWindow
from menu_drawer import Menu, MenuElement, TextElement, MenuOption, Alignment, MenuOptionConfig, draw_menu, \
    HorizontalMenu, BoxedElement, InputHandler
import os


class AnyCompleter(Completer):
    def __init__(self, options: list[str]):
        super().__init__()
        self.options = options

    def get_completions(self, document, complete_event):
        text = document.text
        for option in self.options:
            if option.lower().startswith(text.lower()):
                yield Completion(option, start_position=-len(text))


def select_airport() -> str:
    os.system('cls') # Clear screen for Windows
    country_completer = AnyCompleter(game.get_country_names())
    country_name = safe_prompt("Please select a country: ", completer=country_completer)
    airport_names = game.get_airport_names(country_name)
    selected_airport_name = draw_menu(VerticalMenu([BoxedElement(MenuOption(name, name)) for name in airport_names]))
    return selected_airport_name


def handle_main_view(main_view: MainView, battery: int, distance_km: float) -> str | None:
    main_view.set_battery(battery)
    main_view.set_distance(distance_km)

    while True:
        result = draw_menu(main_view)
        if result is MainViewResult.TAKEOFF:
            selected_airport = select_airport()
            return selected_airport
        elif result is MainViewResult.QUIT:
            game.save_game()
            return None


def handle_challenge(challenge: OpenQuestion | MultipleChoiceQuestion) -> bool:
    match challenge:
        case OpenQuestion(question, answer):
            os.system('cls')
            print(question)
            user_answer = input()
            is_correct = user_answer.lower() == answer.lower()
            print(f"{'Correct!' if is_correct else f'Wrong! The correct answer was: {answer}'}")
            input("press enter to continue...")
            return is_correct
        case MultipleChoiceQuestion(question, options):
            multiple_choice_menu = MultipleChoiceWindow(challenge)
            is_correct = draw_menu(multiple_choice_menu)
            return is_correct
    raise ValueError("Unknown challenge type")


class GameResult(Enum):
    VICTORY = auto()
    DEFEAT = auto()
    QUIT = auto()


def handle_main_loop() -> GameResult:
    main_view = MainView()
    battery = 100

    while True:
        distance = game.get_distance_to_goal_km()
        airport = handle_main_view(main_view, battery, distance)

        if airport is None:
            return GameResult.QUIT

        airport_change_result = game.change_airport(airport)
        battery = airport_change_result.current_battery

        if airport_change_result.is_boss:
            return GameResult.VICTORY  # TODO: add boss challenge handling

        challenge = game.get_challenge()
        passed = handle_challenge(challenge)
        battery = game.challenge_complete(passed)

        if battery <= 0:
            return GameResult.DEFEAT


class GameStartResult(Enum):
    NEW_GAME = auto()
    CONTINUE = auto()
    QUIT = auto()


def configure_game():
    config = MenuOptionConfig(width=20)
    new_game_menu = HorizontalMenu([
        BoxedElement(MenuOption("New Game", GameStartResult.NEW_GAME, config)),
        BoxedElement(MenuOption("Continue", GameStartResult.CONTINUE, config)),
        BoxedElement(MenuOption("Quit", GameStartResult.QUIT, config)),
    ])

    difficulty_menu = HorizontalMenu([
        BoxedElement(MenuOption("Easy", Difficulty.EASY, config)),
        BoxedElement(MenuOption("Medium", Difficulty.MEDIUM, config)),
        BoxedElement(MenuOption("Hard", Difficulty.HARD, config)),
    ])

    while True:
        game_start_result = draw_menu(new_game_menu)
        if game_start_result == GameStartResult.NEW_GAME:
            user_name = input("enter user name: ")
            difficulty = draw_menu(difficulty_menu)
            starting_airport = select_airport()
            game.start_game(user_name, starting_airport, difficulty)
            return
        elif game_start_result == GameStartResult.CONTINUE:
            user_name = input("enter user name: ")
            load_success = game.load_game(user_name)
            if load_success:
                return
            else:
                print("No saved game found.")
                input("press enter to continue...")
                continue
        elif game_start_result == GameStartResult.QUIT:
            exit(0)


while True:
    configure_game()

    game_result = handle_main_loop()
    if game_result == GameResult.QUIT:
        continue
    elif game_result == GameResult.VICTORY:
        print("Congratulations! You've won the game!")
    elif game_result == GameResult.DEFEAT:
        print("Game Over. Better luck next time!")
    input("Press Enter to continue...")