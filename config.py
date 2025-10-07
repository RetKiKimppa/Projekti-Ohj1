import os
from dotenv import load_dotenv
from data import Difficulty

load_dotenv()


class Config:
    DB_HOST = os.getenv('DB_HOST', 'mysql.metropolia.fi')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'project_03')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))

    # Game settings ?
    DEFAULT_BATTERY = int(os.getenv('DEFAULT_BATTERY', '100'))

    BATTERY_CONSUMPTION_PER_GUESS = int(os.getenv('BATTERY_CONSUMPTION_PER_GUESS', '10'))
    BATTERY_REWARD_PER_PUZZLE = int(os.getenv('BATTERY_REWARD_PER_PUZZLE', '15'))

    STARTING_BATTERY_BY_DIFFICULTY = {
        Difficulty.EASY: int(os.getenv('STARTING_BATTERY_EASY', '100')),
        Difficulty.MEDIUM: int(os.getenv('STARTING_BATTERY_MEDIUM', '95')),
        Difficulty.HARD: int(os.getenv('STARTING_BATTERY_HARD', '90')),
    }

    BATTERY_CONSUMPTION_BY_DIFFICULTY = {
        Difficulty.EASY: int(os.getenv('BATTERY_CONSUMPTION_EASY', '10')),
        Difficulty.MEDIUM: int(os.getenv('BATTERY_CONSUMPTION_MEDIUM', '15')),
        Difficulty.HARD: int(os.getenv('BATTERY_CONSUMPTION_HARD', '25')),
    }

    BATTERY_REWARD_PER_PUZZLE_BY_DIFFICULTY = {
        Difficulty.EASY: int(os.getenv('BATTERY_REWARD_EASY', '15')),
        Difficulty.MEDIUM: int(os.getenv('BATTERY_REWARD_MEDIUM', '20')),
        Difficulty.HARD: int(os.getenv('BATTERY_REWARD_HARD', '25')),
    }

    BATTERY_PENALTY_PER_WRONG_ANSWER_BY_DIFFICULTY = {
        Difficulty.EASY: int(os.getenv('BATTERY_PENALTY_EASY', '0')),
        Difficulty.MEDIUM: int(os.getenv('BATTERY_PENALTY_MEDIUM', '5')),
        Difficulty.HARD: int(os.getenv('BATTERY_PENALTY_HARD', '10')),
    }

    DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']

    @classmethod
    def get_starting_battery(cls, difficulty: Difficulty) -> int:
        return cls.STARTING_BATTERY_BY_DIFFICULTY.get(difficulty, 100)

    @classmethod
    def get_battery_consumption(cls, difficulty: Difficulty) -> int:
        return cls.BATTERY_CONSUMPTION_BY_DIFFICULTY.get(difficulty, 10)

    @classmethod
    def get_battery_reward(cls, difficulty: Difficulty) -> int:
        return cls.BATTERY_REWARD_PER_PUZZLE_BY_DIFFICULTY.get(difficulty, 15)

    @classmethod
    def get_battery_penalty(cls, difficulty: Difficulty) -> int:
        return cls.BATTERY_PENALTY_PER_WRONG_ANSWER_BY_DIFFICULTY.get(difficulty, 0)

    @classmethod
    def get_db_config(cls):
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'port': cls.DB_PORT,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True
        }