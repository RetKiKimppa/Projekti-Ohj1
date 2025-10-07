import mysql.connector
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from config import Config
from models import Airport
from data import *


class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**Config.get_db_config())
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: tuple = None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Query exec error: {e}")
            return None

    def execute_update(self, query: str, params: tuple = None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.rowcount
        except mysql.connector.Error as e:
            print(f"Update execution error: {e}")
            return 0


class Player:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.id = None
        self.name = None
        self.current_airport_id = None
        self.battery_level = Config.DEFAULT_BATTERY
        self.difficulty_level = 'easy'
        self.total_score = 0

    def create_or_get_player(self, name: str) -> bool:
        query = "SELECT * FROM player WHERE name = %s"
        result = self.db.execute_query(query, (name,))

        if result:
            player_data = result[0]
            self.id = player_data['id']
            self.name = player_data['name']
            self.current_airport_id = player_data['current_airport_id']
            self.battery_level = player_data['battery_level']
            self.difficulty_level = player_data['difficulty_level']
            self.total_score = player_data['total_score']
            return True
        else:
            query = """INSERT INTO player (name, battery_level, difficulty_level)
                       VALUES (%s, %s, %s)"""
            if self.db.execute_update(query, (name, Config.DEFAULT_BATTERY, 'easy')):
                return self.create_or_get_player(name)
        return False

    def update_battery(self, amount: int):
        self.battery_level = max(0, min(100, self.battery_level + amount))
        query = "UPDATE player SET battery_level = %s WHERE id = %s"
        self.db.execute_update(query, (self.battery_level, self.id))

    def set_difficulty(self, difficulty: str):
        if difficulty in Config.DIFFICULTY_LEVELS:
            self.difficulty_level = difficulty
            query = "UPDATE player SET difficulty_level = %s WHERE id = %s"
            self.db.execute_update(query, (difficulty, self.id))


class Country:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_all_countries(self) -> List[CountryDto]:
        query = "SELECT * FROM country ORDER BY name"
        results = self.db.execute_query(query)
        return [CountryDto.create(row) for row in results] if results else []

    def get_country_by_name(self, name: str) -> Optional[CountryDto]:
        query = "SELECT * FROM country WHERE LOWER(name) = LOWER(%s)"
        result = self.db.execute_query(query, (name,))
        return CountryDto.create(result[0]) if result else None

    def get_country_by_code(self, code: str) -> Optional[Dict]:
        query = "SELECT * FROM country WHERE code = %s"
        result = self.db.execute_query(query, (code,))
        return CountryDto.create(result[0]) if result else None


class Airport:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_airports_by_country(self, country_code: str) -> List[AirportDto]:
        query = """SELECT a.*, c.name as country_name
                   FROM airport a
                            JOIN country c ON a.country_code = c.code
                   WHERE a.country_code = %s
                   ORDER BY a.is_major_hub DESC, a.name"""
        results = self.db.execute_query(query, (country_code,))
        return [AirportDto.create(row) for row in results] if results else []


    def get_airport_by_id(self, airport_id: int) -> Optional[AirportDto]:
        query = """SELECT a.*, c.name as country_name, c.continent
                   FROM airport a
                            JOIN country c ON a.country_code = c.code
                   WHERE a.id = %s"""
        result = self.db.execute_query(query, (airport_id,))
        return AirportDto.create(result[0]) if result else None

    def get_random_airport(self) -> Optional[AirportDto]:
        query = """SELECT a.*, c.name as country_name, c.continent
                   FROM airport a
                            JOIN country c ON a.country_code = c.code
                   WHERE a.is_major_hub = true
                   ORDER BY RAND() LIMIT 1"""
        result = self.db.execute_query(query)
        return AirportDto.create(result[0]) if result else None


class GameSession:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.id = None
        self.player_id = None
        self.difficulty_level = 'easy'
        self.starting_airport_id = None
        self.boss_airport_id = None
        self.boss_country_code = None
        self.current_airport_id = None
        self.battery_level = Config.DEFAULT_BATTERY
        self.puzzles_solved = 0
        self.countries_guessed = []
        self.status = 'active'
        self.score = 0

    def create_new_session(self, player_id: int, difficulty: str, boss_airport: AirportDto) -> bool:
        airport_model = Airport(self.db)
        starting_airport = airport_model.get_random_airport()

        if not starting_airport:
            return False

        query = """INSERT INTO game_session
                   (player_id, difficulty_level, starting_airport_id, boss_airport_id,
                    boss_country_code, current_airport_id, battery_level, countries_guessed)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        countries_json = json.dumps([])

        if self.db.execute_update(query, (
                player_id, difficulty, starting_airport.id, boss_airport.id,
                boss_airport['country_code'], starting_airport.id,
                Config.DEFAULT_BATTERY, countries_json
        )):
            query = "SELECT * FROM game_session WHERE player_id = %s ORDER BY id DESC LIMIT 1"
            result = self.db.execute_query(query, (player_id,))
            if result:
                session_data = result[0]
                self.id = session_data['id']
                self.player_id = session_data['player_id']
                self.difficulty_level = session_data['difficulty_level']
                self.starting_airport_id = session_data['starting_airport_id']
                self.boss_airport_id = session_data['boss_airport_id']
                self.boss_country_code = session_data['boss_country_code']
                self.current_airport_id = session_data['current_airport_id']
                self.battery_level = session_data['battery_level']
                self.puzzles_solved = session_data['puzzles_solved']
                self.countries_guessed = json.loads(session_data['countries_guessed']) if session_data[
                    'countries_guessed'] else []
                self.status = session_data['status']
                self.score = session_data['score']
                return True
        return False

    def add_guessed_country(self, country: CountryDto):
        if country.code not in self.countries_guessed:
            self.countries_guessed.append(country.code)
            query = "UPDATE game_session SET countries_guessed = %s WHERE id = %s"
            self.db.execute_update(query, (json.dumps(self.countries_guessed), self.id))

    def update_current_airport(self, airport: AirportDto):
        self.current_airport_id = airport.id
        query = "UPDATE game_session SET current_airport_id = %s WHERE id = %s"
        self.db.execute_update(query, (airport.id, self.id))

    def update_battery(self, amount: int):
        self.battery_level = max(0, min(100, self.battery_level + amount))
        query = "UPDATE game_session SET battery_level = %s WHERE id = %s"
        self.db.execute_update(query, (self.battery_level, self.id))

    def increment_puzzles_solved(self):
        self.puzzles_solved += 1
        query = "UPDATE game_session SET puzzles_solved = %s WHERE id = %s"
        self.db.execute_update(query, (self.puzzles_solved, self.id))

    def update_status(self, status: GameStatus):
        status_str = status.value if isinstance(status, GameStatus) else status
        self.status = status_str
        completed_at = datetime.now() if status_str in ['won', 'lost', 'abandoned'] else None

        if completed_at:
            query = "UPDATE game_session SET status = %s, completed_at = %s WHERE id = %s"
            self.db.execute_update(query, (status_str, completed_at, self.id))
        else:
            query = "UPDATE game_session SET status = %s WHERE id = %s"
            self.db.execute_update(query, (status_str, self.id))


class Challenge:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_random_open_question(self, difficulty: Difficulty) -> Optional[OpenQuestion]:
        query = """SELECT * \
                   FROM question_task
                   WHERE difficulty_level = %s
                   ORDER BY RAND() LIMIT 1"""
        result = self.db.execute_query(query, (difficulty.value,))
        if result:
            question_data = result[0]
            return OpenQuestion(
                question=question_data['question'],
                answer=question_data['correct_answer']
            )
        return None

    def get_random_multiple_choice(self, difficulty: Difficulty) -> Optional[MultipleChoiceQuestion]:
        query = """SELECT * \
                   FROM multiple_choice_question
                   WHERE difficulty_level = %s
                   ORDER BY RAND() LIMIT 1"""
        result = self.db.execute_query(query, (difficulty.value,))

        if not result:
            return None

        question = result[0]

        query = """SELECT * \
                   FROM multiple_choice_answer
                   WHERE question_id = %s
                   ORDER BY RAND()"""
        answers = self.db.execute_query(query, (question['id'],))

        options = [MultipleChoiceOption(name=ans['answer'], is_correct=ans['is_correct']) for ans in answers] if answers else []
        return MultipleChoiceQuestion(
            question=question['question'],
            options=options
        )


class GameSave:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save_game(self, player_id: int, session: GameSession, save_name: str = "autosave") -> bool:
        game_data = {
            'session_id': session.id,
            'difficulty_level': session.difficulty_level,
            'starting_airport_id': session.starting_airport_id,
            'boss_airport_id': session.boss_airport_id,
            'boss_country_code': session.boss_country_code,
            'current_airport_id': session.current_airport_id,
            'battery_level': session.battery_level,
            'puzzles_solved': session.puzzles_solved,
            'countries_guessed': session.countries_guessed,
            'status': session.status,
            'score': session.score,
            'save_timestamp': datetime.now().isoformat()
        }

        query = "SELECT id FROM game_save WHERE player_id = %s AND save_name = %s"
        existing = self.db.execute_query(query, (player_id, save_name))

        if existing:
            query = """UPDATE game_save
                       SET game_data  = %s, \
                           updated_at = CURRENT_TIMESTAMP
                       WHERE player_id = %s \
                         AND save_name = %s"""
            return self.db.execute_update(query, (json.dumps(game_data), player_id, save_name)) > 0
        else:
            query = """INSERT INTO game_save (player_id, save_name, game_data)
                       VALUES (%s, %s, %s)"""
            return self.db.execute_update(query, (player_id, save_name, json.dumps(game_data))) > 0

    def get_player_saves(self, player_id: int) -> List[Dict]:
        query = """SELECT id, save_name, created_at, updated_at, game_data
                   FROM game_save
                   WHERE player_id = %s
                   ORDER BY updated_at DESC"""
        saves = self.db.execute_query(query, (player_id,))

        if saves:
            for save in saves:
                try:
                    game_data = json.loads(save['game_data'])
                    save['preview'] = {
                        'difficulty': game_data.get('difficulty_level', 'unknown'),
                        'battery': game_data.get('battery_level', 0),
                        'puzzles_solved': game_data.get('puzzles_solved', 0),
                        'countries_guessed': len(game_data.get('countries_guessed', [])),
                        'status': game_data.get('status', 'unknown')
                    }
                except json.JSONDecodeError:
                    save['preview'] = {'error': 'Invalid save data'}

        return saves or []

    def load_game(self, player_id: int, save_name: str) -> Optional[Dict]:
        query = """SELECT game_data \
                   FROM game_save
                   WHERE player_id = %s \
                     AND save_name = %s"""
        result = self.db.execute_query(query, (player_id, save_name))

        if result:
            try:
                return json.loads(result[0]['game_data'])
            except json.JSONDecodeError:
                return None
        return None

    def delete_save(self, player_id: int, save_name: str) -> bool:
        query = "DELETE FROM game_save WHERE player_id = %s AND save_name = %s"
        return self.db.execute_update(query, (player_id, save_name)) > 0

    def restore_session_from_save(self, save_data: Dict, db: DatabaseConnection) -> Optional[GameSession]:
        session = GameSession(db)

        session.id = save_data.get('session_id')
        session.difficulty_level = save_data.get('difficulty_level', 'easy')
        session.starting_airport_id = save_data.get('starting_airport_id')
        session.boss_airport_id = save_data.get('boss_airport_id')
        session.boss_country_code = save_data.get('boss_country_code')
        session.current_airport_id = save_data.get('current_airport_id')
        session.battery_level = save_data.get('battery_level', 100)
        session.puzzles_solved = save_data.get('puzzles_solved', 0)
        session.countries_guessed = save_data.get('countries_guessed', [])
        session.status = save_data.get('status', 'active')
        session.score = save_data.get('score', 0)

        return session