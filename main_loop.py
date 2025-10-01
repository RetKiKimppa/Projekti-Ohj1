from menu_drawer import draw_menu
from main_view import MainView


def select_airport() -> str:
    # country_name = prompt for country name
    # get_airports(country_name)
    # display options as menu
    # return selected airport name


def handle_main_view(main_view: MainView, battery: int, distance_km: float) -> str:
    main_view.set_battery(battery)
    main_view.set_distance(distance_km)

    while True:
        result = draw_menu(main_view)
        # if result takeoff
            # sselect_airport()
            # return airport
        # else keep handling main view


def handle_challenge(challenge) -> bool:
    # if open question
        # prompt for answer
        # check answer
    # if multiple choice
        # show options
        # get choice
        # check choice
    return True  # return True if passed, False otherwise


def handle_main_loop() -> bool:
    # main_view = MainView()
    # battery = 100

    while True:
        # distance = get_distance_to_goal_km()
        # airport = handle_main_view(main_view, battery, distance)
        # airport_change_result = change_airport(airport)
        # battery = airport_change_result.current_battery

        # if airport_change_result.is_boss:
            # return handle_boss_challenge()

        # challenge = get_challenge()
        # passed = handle_challenge(challenge)
        # battery = challenge_completed(passed)

        # if battery <= 0:
            # return false


def configure_game():
    while True
        # display new game and continue
        # if new game
            # user_name = input("name: ")
            # difficulty = display difficulty menu
            # starting_airport = select_airport()
            # start_game(user_name, starting_airport, difficulty)
            # return
        # else
            # user_name = input("name: ")
            # load_success = load_game(user_name)
            # if load_success
                # return
            # else:
                # print("No saved game found.")
                # continue


while True:
    # configure_game()

    victory = handle_main_loop()
    # handle victory display and replay option







