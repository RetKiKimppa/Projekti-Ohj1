from data import *
from models_new import (DatabaseConnection, Player, Country, Airport,
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
        self.game_save: GameSave | None = None

    def initialize(self) -> ResultNoValue:
        if not self.db.connect():
            return ResultNoValue.failure("Database connection failed.")
        return ResultNoValue.success()

    def terminate(self):
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

        self.player.set_battery(Config.get_starting_battery(difficulty))
        self.player.set_difficulty(difficulty)

        self.current_session = GameSession(self.db)
        if not self.current_session.create_new_session(
                self.player.id, self.player.difficulty_level, self.boss_airport):
            return ResultNoValue.failure("Could not create game session.")

        self.current_session.update_current_airport(starting_airport)
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
        self.current_session.add_guessed_country(country)
        self.current_session.update_current_airport(airport)
        self.auto_save_game()
        if airport.id == self.boss_airport.id:
            return FlightResult.CORRECT_AIRPORT
        elif airport.country_code == self.boss_airport.country_code:
            return FlightResult.CORRECT_COUNTRY
        else:
            return FlightResult.INCORRECT

    def auto_save_game(self):
        """Automatically save the game"""
        if self.current_session and self.current_session.status == 'active':
            self.game_save.save_game(self.player.id, self.current_session, "autosave")

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

        lat1, lon1 = math.radians(float(current_airport.latitude)), math.radians(float(current_airport.longitude))
        lat2, lon2 = math.radians(float(goal_airport.latitude)), math.radians(float(goal_airport.longitude))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        r = 6371

        return r * c