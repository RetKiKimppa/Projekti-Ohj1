from enum import Enum, auto
from game_new import BossFlightGameDriver
from prompt_utils import safe_prompt
from prompt_toolkit.completion import Completer, Completion
from menu_drawer import draw_menu, VerticalMenu
from menu_windows import MainView, MainViewResult, MultipleChoiceWindow
from menu_drawer import Menu, MenuElement, TextElement, MenuOption, Alignment, MenuOptionConfig, draw_menu, \
    HorizontalMenu, BoxedElement, InputHandler
import os
from data import *


class AnyCompleter(Completer):
    def __init__(self, options: list[str]):
        super().__init__()
        self.options = options

    def get_completions(self, document, complete_event):
        text = document.text
        for option in self.options:
            if option.lower().startswith(text.lower()):
                yield Completion(option, start_position=-len(text))


def prompt_country(game: BossFlightGameDriver) -> str:
    os.system('cls') # Clear screen for Windows
    country_names = game.get_all_country_names()
    country_completer = AnyCompleter(country_names)
    while True:
        country_name = safe_prompt("Please select a country: ", completer=country_completer)
        if country_name in country_names:
            return country_name
        else:
            print(f"'{country_name}' is not a valid country. Please try again.")


def prompt_airport(game: BossFlightGameDriver, country_name: str) -> str | None:
    airport_names = game.get_airport_names(country_name)
    if not airport_names:
        return None
    selected_airport_name = draw_menu(VerticalMenu([BoxedElement(MenuOption(name, name)) for name in airport_names]))
    return selected_airport_name


def select_airport(game: BossFlightGameDriver) -> str:
    while True:
        country_name = prompt_country(game)
        airport_name = prompt_airport(game, country_name)
        if airport_name:
            return airport_name
        else:
            print(f"No airports found in {country_name}. Please select another country.")


def handle_challenge(challenge: OpenQuestion | MultipleChoiceQuestion) -> ChallengeResult:
    match challenge:
        case OpenQuestion(question, answer):
            os.system('cls')
            print(question)
            user_answer = input()
            is_correct = user_answer.lower() == answer.lower()
            print(f"{'Correct!' if is_correct else f'Wrong! The correct answer was: {answer}'}")
            return ChallengeResult.CORRECT if is_correct else ChallengeResult.INCORRECT
        case MultipleChoiceQuestion(question, options):
            multiple_choice_menu = MultipleChoiceWindow(challenge)
            is_correct = draw_menu(multiple_choice_menu)
            correct_answer = next((opt.name for opt in options if opt.is_correct), "Unknown")
            print(f"{'Correct!' if is_correct else f'Wrong! The correct answer was: {correct_answer}'}")
            return ChallengeResult.CORRECT if is_correct else ChallengeResult.INCORRECT
    raise ValueError("Unknown challenge type")

class GameResult(Enum):
    VICTORY = auto()
    DEFEAT = auto()
    QUIT = auto()

class GameStartResult(Enum):
    NEW_GAME = auto()
    CONTINUE = auto()
    QUIT = auto()


def configure_game(game: BossFlightGameDriver) -> ResultNoValue:
    player_setup_result = setup_player(game)
    if not player_setup_result.is_success():
        return player_setup_result

    while True:
        main_menu_result = main_menu(game)
        match main_menu_result:
            case GameStartResult.NEW_GAME:
                difficulty = select_difficulty()
                starting_airport = select_airport(game)
                start_result = game.start_new_game(starting_airport, difficulty)
                return start_result
            case GameStartResult.CONTINUE:
                # TODO: Handle saved games thorugh menu
                if not try_load_game(game):
                    return ResultNoValue.failure("No saved game found.")
                return ResultNoValue.success()
            case GameStartResult.QUIT:
                game.terminate()
                exit(0)

def try_load_game(game: BossFlightGameDriver) -> ResultNoValue:
    user_name = game.player.name
    return ResultNoValue.failure("No saved game found.")

def display_introduction() -> None:
    print("Welcome to Boss Flights 🛩️")
    print("=" * 50)
    print("Your mission: Find the boss's secret airport by guessing countries!")
    print("Solve puzzles to gain battery, but be careful - wrong guesses drain power!")
    print("=" * 50)
    input("Press Enter to continue...")

def setup_player(game: BossFlightGameDriver) -> ResultNoValue:
    name = input("\nEnter your pilot name: ")
    if not name:
        name = "Anonymous Pilot"

    # TODO: Incorporate this as text elements in main menu
    if game.setup_player(name):
        print(f"\nWelcome back, Captain {name}!")
        input("Press Enter to continue...")
    else:
        return ResultNoValue.failure("Could not create player profile.")
    return ResultNoValue.success()

def main_menu(game: BossFlightGameDriver) -> GameStartResult:
    config = MenuOptionConfig(width=20)
    new_game_menu = HorizontalMenu([
        BoxedElement(MenuOption("New Game", GameStartResult.NEW_GAME, config)),
        BoxedElement(MenuOption("Continue", GameStartResult.CONTINUE, config)),
        BoxedElement(MenuOption("Quit", GameStartResult.QUIT, config)),
    ])
    game_start_result = draw_menu(new_game_menu)
    return game_start_result

def select_difficulty() -> Difficulty:
    config = MenuOptionConfig(width=20)
    difficulty_menu = HorizontalMenu([
        BoxedElement(MenuOption("Easy", Difficulty.EASY, config)),
        BoxedElement(MenuOption("Medium", Difficulty.MEDIUM, config)),
        BoxedElement(MenuOption("Hard", Difficulty.HARD, config)),
    ])
    difficulty = draw_menu(difficulty_menu)
    return difficulty


def handle_flight(game: BossFlightGameDriver) -> FlightResult:
    selected_airport = select_airport(game)
    flight_result = game.change_airport(selected_airport)
    challenge = game.get_challenge()
    if not challenge:
        raise ValueError("No challenge available")
    challenge_result = handle_challenge(challenge)
    battery_change = game.challenge_completed(challenge_result)
    match challenge_result:
        case ChallengeResult.CORRECT:
            print(f"Battery increased by {battery_change}.")
        case ChallengeResult.INCORRECT:
            print(f"Battery decreased by {-battery_change}.")
    input("Press Enter to continue...")
    return flight_result


def game_loop(game: BossFlightGameDriver):
    while game.current_session.status is SessionStatus.ACTIVE:
        player_name = game.player.name
        battery_percentage = game.current_session.battery_level
        main_view = MainView(player_name)

        while True:
            distance = game.get_distance_to_goal_km()
            main_view.set_battery(battery_percentage)
            main_view.set_distance(distance)

            main_view_result = draw_menu(main_view)
            match main_view_result:
                case MainViewResult.TAKEOFF:
                    flight_result = handle_flight(game)
                    continue
                case MainViewResult.QUIT:
                    game.terminate() # TODO: Add handling for game saving
                    exit(0)


def main():
    game: BossFlightGameDriver = BossFlightGameDriver()
    init_result = game.initialize()
    if not init_result.is_success():
        print(f"Error: {init_result.error}")
        return

    try:
        display_introduction()
        configure_game(game)

        game_loop(game)
    finally:
        game.terminate()

if __name__ == '__main__':
    main()