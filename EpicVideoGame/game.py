import airport_util
from data import *
from models import (DatabaseConnection, Player, Country, Airport,
                    GameSession, Challenge, GameSave)
from config import Config
import random
import math
from typing import Dict, List, Optional, Tuple



class BossFlightGameDriver:
    def __init__(self):
        self.db: DatabaseConnection = DatabaseConnection()
        self.player: Player | None = None
        self.current_session: GameSession | None = None
        self.boss_airport: AirportDto | None = None
        self.current_airport: AirportDto | None = None
        self.current_country: CountryDto | None = None
        self.game_save: GameSave | None = None
        self.current_save: GameSaveDto | None = None
        self.correct_continent: str | None = None
        self.correct_country: str | None = None

    def initialize(self) -> ResultNoValue:
        if not self.db.connect():
            return ResultNoValue.failure("Database connection failed.")
        return ResultNoValue.success()

    def terminate(self):
        self.auto_save_game()
        self.db.disconnect()

    def setup_player(self, player_name: str) -> bool:
        self.player = Player(self.db)
        if self.player.create_or_get_player(player_name):
            self.game_save = GameSave(self.db)
            return True
        else:
            return False

    def start_new_game(self, starting_airport_name: str, difficulty: Difficulty) -> ResultNoValue:
        """Start a new game session"""
        airport_model = Airport(self.db)

        self.boss_airport = airport_model.get_random_airport()
        if not self.boss_airport:
            return ResultNoValue.failure("No airports available in the database.")

        starting_airport = airport_model.get_airport_by_name(starting_airport_name)
        if not starting_airport:
            return ResultNoValue.failure(f"Starting airport '{starting_airport_name}' not found.")

        starting_country = Country(self.db).get_country_by_code(starting_airport.country_code)
        self.current_country = starting_country
        self.current_airport = airport_model.get_airport_by_name(starting_airport_name)

        self.player.set_battery(Config.get_starting_battery(difficulty))
        self.player.set_difficulty(difficulty)

        self.current_session = GameSession(self.db)
        if not self.current_session.create_new_session(
                self.player.id, self.player.difficulty_level, self.boss_airport):
            return ResultNoValue.failure("Could not create game session.")

        self.current_session.update_current_airport(starting_airport)
        return ResultNoValue.success()

    def get_saves(self) -> List[GameSaveDto]:
        if not self.player:
            return []
        saves = self.game_save.get_player_saves(self.player.id)
        if not saves:
            return []
        return saves

    def load_save(self, save: GameSaveDto) -> ResultNoValue:
        save_data = self.game_save.load_game(save)
        if not save_data:
            return ResultNoValue.failure("Failed to load save data.")
        self.current_session = self.game_save.restore_session_from_save(save_data, self.db)
        if not self.current_session:
            return ResultNoValue.failure("Failed to restore game session from save data.")

        airport_model = Airport(self.db)
        self.current_airport = airport_model.get_airport_by_id(self.current_session.current_airport_id)
        if not self.current_airport:
            return ResultNoValue.failure("Failed to find current airport from session data.")
        self.boss_airport = airport_model.get_airport_by_id(self.current_session.boss_airport_id)
        if not self.boss_airport:
            return ResultNoValue.failure("Failed to find boss airport from session data.")

        country_model = Country(self.db)
        self.current_country = country_model.get_country_by_code(self.current_airport.country_code)
        if not self.current_country:
            return ResultNoValue.failure("Failed to find current country from airport data.")

        if self.current_session.status != 'active':
            return ResultNoValue.failure("Cannot load a game that is not active.")

        self.current_save = save
        return ResultNoValue.success()

    def get_all_country_names(self) -> List[str]:
        country_model = Country(self.db)
        countries = country_model.get_all_countries()
        return [country.name for country in countries]

    def get_country_by_name(self, country_name: str) -> Result[CountryDto]:
        country_model = Country(self.db)
        country = country_model.get_country_by_name(country_name)
        if not country:
            return Result[CountryDto].failure(f"Country '{country_name}' not found.")
        return Result[CountryDto].success(country)

    def get_guessed_countries(self) -> List[CountryDto]:
        if not self.current_session:
            return []
        return self.current_session.countries_guessed

    def get_airport_names(self, country_name: str) -> List[str]:
        country_result = self.get_country_by_name(country_name)
        if not country_result.is_success():
            return []

        country = country_result.value
        airport_model = Airport(self.db)
        airports = airport_model.get_airports_by_country(country)
        return [airport.name for airport in airports]

    def change_airport(self, airport_name: str) -> FlightResult:
        airport = Airport(self.db).get_airport_by_name(airport_name)
        country = Country(self.db).get_country_by_code(airport.country_code)
        if not airport or not country or not self.current_session or not self.boss_airport:
            raise ValueError("Invalid airport or game session state.")

        self.current_country = country
        self.current_airport = airport
        self.current_session.deduct_battery(Config.get_battery_consumption(self.current_session.difficulty_level))
        self.current_session.add_guessed_country(country)
        self.current_session.update_current_airport(airport)
        self.auto_save_game()
        if airport.id == self.boss_airport.id:
            return FlightResult.CORRECT_AIRPORT
        elif airport.country_code == self.boss_airport.country_code:
            return FlightResult.CORRECT_COUNTRY
        elif airport.continent == self.boss_airport.continent:
            return FlightResult.CORRECT_CONTINENT
        else:
            return FlightResult.INCORRECT

    def auto_save_game(self):
        """Automatically save the game"""
        if self.current_session and self.current_session.status == 'active':
            self.game_save.save_game(self.player.id, self.current_session, "autosave")
            saves = self.game_save.get_player_saves(self.player.id)
            autosave = next((s for s in saves if s.save_name == "autosave"), None)
            if autosave:
                self.current_save = autosave

    def get_challenge(self) -> OpenQuestion | MultipleChoiceQuestion | None:
        challenge_model = Challenge(self.db)
        challenge_type = random.choice([ChallengeType.OPEN_QUESTION, ChallengeType.MULTIPLE_CHOICE])
        match challenge_type:
            case ChallengeType.OPEN_QUESTION:
                return challenge_model.get_random_open_question(self.player.difficulty_level)
            case ChallengeType.MULTIPLE_CHOICE:
                return challenge_model.get_random_multiple_choice(self.player.difficulty_level)
        return None

    def challenge_completed(self, challenge_result: ChallengeResult) -> int:
        """Returns battery change (positive or negative)"""
        match challenge_result:
            case ChallengeResult.CORRECT:
                self.current_session.increment_puzzles_solved()
                battery_reward = Config.get_battery_reward(self.current_session.difficulty_level)
                self.current_session.add_battery(battery_reward)
                return battery_reward
            case ChallengeResult.INCORRECT:
                battery_penalty = Config.get_battery_penalty(self.current_session.difficulty_level)
                self.current_session.deduct_battery(battery_penalty)
                return -battery_penalty

    def get_distance_to_goal_km(self) -> float:
        """Get distance to boss airport from current airport"""
        goal_airport = self.boss_airport
        if not self.current_session or not goal_airport:
            return float('inf')

        airport_model = Airport(self.db)
        current_airport = airport_model.get_airport_by_id(self.current_session.current_airport_id)
        if not current_airport:
            return float('inf')

        distance = airport_util.calculate_distance_km(current_airport, goal_airport)
        return distance

    def get_direction_to_goal(self) -> airport_util.CompassDirection:
        """Get direction to boss airport from current airport"""
        goal_airport = self.boss_airport
        if not self.current_session or not goal_airport:
            return airport_util.CompassDirection.N

        direction = airport_util.get_direction(self.current_airport, goal_airport)
        return direction

    def end_game(self, game_result: GameResult):
        if not self.current_session:
            return

        session_status = SessionStatus.ABANDONED
        match game_result:
            case GameResult.VICTORY:
                session_status = SessionStatus.WON
            case GameResult.DEFEAT:
                session_status = SessionStatus.LOST
            case GameResult.QUIT:
                session_status = SessionStatus.ABANDONED

        self.current_session.update_status(session_status)
        if game_result == GameResult.QUIT:
            self.auto_save_game()
        else:
            if self.current_save:
                self.game_save.delete_save(self.current_save)
            self.current_save = None

        self.current_session = None
        self.current_airport = None
        self.current_country = None
        self.boss_airport = None
        self.correct_continent = None
        self.correct_country = None

