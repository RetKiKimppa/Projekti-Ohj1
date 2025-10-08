from game import BossFlightGameDriver
from prompt_utils import safe_prompt
from prompt_toolkit.completion import Completer, Completion
from menu_windows import MainView, MainViewResult, MultipleChoiceWindow, TextWindow
from menu_drawer import TextElement, MenuOption, Alignment, MenuOptionConfig, draw_menu, \
    HorizontalMenu, BoxedElement, VerticalMenu
import os
from data import *
from config import Config

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
    os.system('cls')  # Clear screen for Windows
    country_names = game.get_all_country_names()
    lowered_country_names = [name.lower() for name in country_names]
    country_completer = AnyCompleter(country_names)
    while True:
        guessed_countries = game.get_guessed_countries()
        if guessed_countries:
            guessed_country_names = [country.name for country in guessed_countries]
            print("\nCountries you've already visited:")
            print((", ".join(guessed_country_names) if guessed_country_names else "None"))
        country_name = safe_prompt("\nPlease select a country: ", completer=country_completer).strip()
        if country_name.lower() in lowered_country_names:
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


def handle_challenge(game: BossFlightGameDriver, challenge: OpenQuestion | MultipleChoiceQuestion) -> ChallengeResult:
    correct_answer: str = ""
    is_correct: bool = False
    match challenge:
        case OpenQuestion(question, answer):
            os.system('cls')
            print(f"\n{question}")
            user_answer = input("Your answer: ").strip()
            is_correct = user_answer.lower() == answer.lower()
            correct_answer = answer
        case MultipleChoiceQuestion(question, options):
            multiple_choice_menu = MultipleChoiceWindow(challenge)
            is_correct = draw_menu(multiple_choice_menu)
            correct_answer = next((opt.name for opt in options if opt.is_correct), "Unknown")
    challenge_result: ChallengeResult = ChallengeResult.CORRECT if is_correct else ChallengeResult.INCORRECT
    battery_change = game.challenge_completed(challenge_result)
    message = "Correct!" if is_correct else f"Wrong. The correct answer was: {correct_answer}"
    result_window = TextWindow(
        [TextElement(message, width=60, alignment=Alignment.CENTER),
            TextElement(f"Battery {'increased' if battery_change > 0 else 'decreased'} by {abs(battery_change)}%", width=60, alignment=Alignment.CENTER),
         TextElement("Press any key to continue...", width=60, alignment=Alignment.CENTER, offset_y=1)]
    )
    draw_menu(result_window)
    return ChallengeResult.CORRECT if is_correct else ChallengeResult.INCORRECT

def handle_continue_menu(game: BossFlightGameDriver) -> bool:
    back_str = "Back"
    saves = game.get_saves()
    save_names = [save.save_name for save in saves]
    save_elements = [BoxedElement(MenuOption(name, name, MenuOptionConfig(width=30))) for name in save_names]
    elements = [BoxedElement(MenuOption(back_str, back_str))]
    elements.extend(save_elements)
    save_menu = HorizontalMenu(elements, start_y=4)
    save_menu.add_non_selectable([TextElement(f"Pilot: {game.player.name}", alignment=Alignment.LEFT)], -1)
    selected_save = draw_menu(save_menu)
    if selected_save == back_str:
        return False
    selected_save_obj = next((save for save in saves if save.save_name == selected_save), None)
    if not selected_save_obj:
        return False
    load_result = game.load_save(selected_save_obj)
    if not load_result.is_success():
        error_window = TextWindow([
            TextElement(f"Error loading save: {load_result.error}", alignment=Alignment.CENTER),
            TextElement("Press any key to continue...", alignment=Alignment.CENTER, offset_y=1)
        ])
        draw_menu(error_window)
        return False
    return True



def handle_main_menu(game: BossFlightGameDriver) -> ResultNoValue:
    while True:
        main_menu_result = main_menu(game.player.name)
        match main_menu_result:
            case MainMenuResult.NEW_GAME:
                difficulty = select_difficulty()
                starting_airport = select_airport(game)
                start_result = game.start_new_game(starting_airport, difficulty)
                return start_result
            case MainMenuResult.CONTINUE:
                loaded_game = handle_continue_menu(game)
                if not loaded_game:
                    continue
                return ResultNoValue.success()
            case MainMenuResult.CHANGE_PILOT:
                player_setup_result = setup_player(game)
                if not player_setup_result.is_success():
                    return player_setup_result
            case MainMenuResult.QUIT:
                game.terminate()
                exit(0)


def display_introduction() -> None:
    intro_window = TextWindow([
        TextElement("Welcome to Boss Flights", alignment=Alignment.CENTER),
        TextElement("Find the boss's secret airport.", alignment=Alignment.CENTER),
        TextElement(""),
        TextElement("Select a country and airport.", alignment=Alignment.CENTER),
        TextElement("Answer questions for battery.", alignment=Alignment.CENTER),
        TextElement("Win by finding the secret airport.", alignment=Alignment.CENTER),
        TextElement("Press any key to continue...", alignment=Alignment.CENTER, offset_y=1)
    ], autosize_to_highest_width=True)
    draw_menu(intro_window)


def setup_player(game: BossFlightGameDriver) -> ResultNoValue:
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    name = input("\nEnter your pilot name: ")
    if not name:
        name = "Anonymous Pilot"

    # TODO: Incorporate this as text elements in main menu
    if game.setup_player(name):
        return ResultNoValue.success()
    else:
        return ResultNoValue.failure("Could not create player profile.")


def main_menu(player_name: str) -> MainMenuResult:
    config = MenuOptionConfig(width=20)
    new_game_menu = HorizontalMenu([
        BoxedElement(MenuOption("New Game", MainMenuResult.NEW_GAME, config)),
        BoxedElement(MenuOption("Continue", MainMenuResult.CONTINUE, config)),
        BoxedElement(MenuOption("Change Pilot", MainMenuResult.CHANGE_PILOT, config)),
        BoxedElement(MenuOption("Quit", MainMenuResult.QUIT, config))],
        start_y=4
    )
    new_game_menu.add_non_selectable([TextElement(f"Pilot: {player_name}", alignment=Alignment.CENTER)], -1)
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
    challenge_result = handle_challenge(game, challenge)
    return flight_result


def after_flight_message(result: FlightResult, game: BossFlightGameDriver) -> None:
    difficulty = game.current_session.difficulty_level
    correct_continent = game.correct_continent
    correct_country = game.correct_country
    message: str = ""
    match result:
        case FlightResult.INCORRECT:
            return
        case FlightResult.CORRECT_CONTINENT:
            if not Config.allow_show_correct_continent(difficulty) or correct_continent is not None:
                return
            message = "You can feel the presence of the boss - you're in the correct continent!"
        case FlightResult.CORRECT_COUNTRY:
            if not Config.allow_show_correct_country(difficulty) or correct_country is not None:
                return
            message = "The boss is near - you've arrived in the correct country!"
        case FlightResult.CORRECT_AIRPORT:
            message = "Congratulations! You've found the boss's secret airport!"

    if message == "":
        return

    result_window = TextWindow([
        TextElement(message, alignment=Alignment.CENTER),
        TextElement("Press any key to continue...", alignment=Alignment.CENTER, offset_y=1)
    ])
    draw_menu(result_window)


def show_correct_info(main_view: MainView, difficulty: Difficulty, country: bool, continent: bool):
    if country and Config.allow_show_correct_country(difficulty):
        main_view.show_correct_country(True)
    else:
        main_view.show_correct_country(False)
    if continent and Config.allow_show_correct_continent(difficulty):
        main_view.show_correct_continent(True)
    else:
        main_view.show_correct_continent(False)

def game_loop(game: BossFlightGameDriver):
    player_name = game.player.name
    main_view = MainView(player_name)
    main_view.show_direction = True if game.current_session.difficulty_level != Difficulty.HARD else False
    main_view.set_difficulty(game.current_session.difficulty_level)

    while game.current_session.status is SessionStatus.ACTIVE:
        distance = game.get_distance_to_goal_km()
        airport_name = game.current_airport.name
        country_name = game.current_country.name
        continent_name = game.current_country.continent
        direction = game.get_direction_to_goal()
        main_view.set_airport(airport_name)
        main_view.set_country(country_name)
        main_view.set_continent(continent_name)
        main_view.set_battery(game.current_session.battery_level)
        main_view.set_direction(direction)
        main_view.set_distance(distance)

        main_view_result = draw_menu(main_view)
        match main_view_result:
            case MainViewResult.TAKEOFF:
                flight_result = handle_flight(game)
                after_flight_message(flight_result, game)
                if flight_result == FlightResult.CORRECT_AIRPORT:
                    game.end_game(GameResult.VICTORY)
                    return
                elif flight_result == FlightResult.CORRECT_COUNTRY:
                    game.correct_country = game.current_country.name
                    show_correct_info(main_view, game.current_session.difficulty_level, True, True)
                elif flight_result == FlightResult.CORRECT_CONTINENT:
                    game.correct_continent = game.current_country.continent
                    show_correct_info(main_view, game.current_session.difficulty_level, country=False, continent=True)
                elif flight_result == FlightResult.INCORRECT:
                    show_correct_info(main_view, game.current_session.difficulty_level, country=False, continent=False)
                    if game.current_session.battery_level <= 0:
                        lose_display = TextWindow([
                            TextElement("Game Over!", alignment=Alignment.CENTER),
                            TextElement("You've run out of battery!", alignment=Alignment.CENTER),
                            TextElement("Press any key to continue...", alignment=Alignment.CENTER, offset_y=1)
                        ])
                        draw_menu(lose_display)
                        game.end_game(GameResult.DEFEAT)
                        return
            case MainViewResult.QUIT:
                game.end_game(GameResult.QUIT)  # TODO: Add handling for game saving
                return


def start_loop():
    os.system('cls' if os.name == 'nt' else 'clear')
    game: BossFlightGameDriver = BossFlightGameDriver()
    init_result = game.initialize()
    if not init_result.is_success():
        print(f"Error: {init_result.error}")
        return

    try:
        display_introduction()
        player_setup_result = setup_player(game)
        if not player_setup_result.is_success():
            print(f"Error: {player_setup_result.error}")
            return

        while True:
            handle_main_menu(game)
            game_loop(game)
    finally:
        game.terminate()


def main():
    try:
        start_loop()
    except KeyboardInterrupt:
        print("\n\n✈️  Game stopped!")
    except Exception as e:
        print (f"\n Error during execution: {e}")
        raise e


if __name__ == "__main__":
    main()