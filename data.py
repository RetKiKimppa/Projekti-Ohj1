from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self.value = value
        self.error = error

    def is_success(self) -> bool:
        return self.error is None

    def is_error(self) -> bool:
        return self.error is not None

    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        return cls(value=value)

    @classmethod
    def failure(cls, error: str) -> 'Result[T]':
        return cls(error=error)

class ResultNoValue:
    def __init__(self, error: Optional[str] = None):
        self.error = error

    def is_success(self) -> bool:
        return self.error is None

    def is_error(self) -> bool:
        return self.error is not None

    @classmethod
    def success(cls) -> 'ResultNoValue':
        return cls()

    @classmethod
    def failure(cls, error: str) -> 'ResultNoValue':
        return cls(error=error)

class GameResult(Enum):
    VICTORY = auto()
    DEFEAT = auto()
    QUIT = auto()

class MainMenuResult(Enum):
    NEW_GAME = auto()
    CONTINUE = auto()
    CHANGE_PILOT = auto()
    QUIT = auto()

class SessionStatus(Enum):
    ACTIVE = 'active'
    WON = 'won'
    LOST = 'lost'
    ABANDONED = 'abandoned'

class Difficulty(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class ChallengeResult(Enum):
    CORRECT = 'correct'
    INCORRECT = 'incorrect'

class ChallengeType(Enum):
    OPEN_QUESTION = 'open_question'
    MULTIPLE_CHOICE = 'multiple_choice'

@dataclass
class OpenQuestion:
    question: str
    answer: str

@dataclass
class MultipleChoiceOption:
    name: str
    is_correct: bool

@dataclass
class MultipleChoiceQuestion:
    question: str
    options: list[MultipleChoiceOption]

class FlightResult(Enum):
    CORRECT_AIRPORT = 'correct_airport'
    CORRECT_COUNTRY = 'correct_country'
    CORRECT_CONTINENT = 'correct_continent'
    INCORRECT = 'incorrect'

@dataclass
class AirportDto:
    id: int
    icao_code: str
    iata_code: str
    name: str
    city: str
    country_code: str
    latitude: float
    longitude: float
    elevation_ft: int
    continent: str

    @classmethod
    def create(cls, Dict):
        id = Dict.get('id', 0)
        icao_code = Dict.get('icao_code', '')
        iata_code = Dict.get('iata_code', '')
        name = Dict.get('name', '')
        city = Dict.get('city', '')
        country_code = Dict.get('country_code', '')
        latitude = Dict.get('latitude', 0.0)
        longitude = Dict.get('longitude', 0.0)
        elevation_ft = Dict.get('elevation_ft', 0)
        continent = Dict.get('continent', '')

        if not id or not icao_code or not iata_code or not name or not city or not country_code or not continent:
            raise ValueError("Invalid airport data")

        return cls(
            id=id,
            icao_code=icao_code,
            iata_code=iata_code,
            name=name,
            city=city,
            country_code=country_code,
            latitude=latitude,
            longitude=longitude,
            elevation_ft=elevation_ft,
            continent=continent
        )

@dataclass
class CountryDto:
    code: str
    name: str
    continent: str

    @classmethod
    def create(cls, Dict):
        code = Dict.get('code', '')
        name = Dict.get('name', '')
        continent = Dict.get('continent', '')

        if not code or not name or not continent:
            raise ValueError("Invalid country data")

        return cls(
            code=code,
            name=name,
            continent=continent
        )


@dataclass
class GameSaveDto:
    id: int
    player_id: int
    save_name: str

    @classmethod
    def create(cls, Dict) -> 'GameSaveDto':
        return cls(
            id=Dict.get('id', 0),
            player_id=Dict.get('player_id', 0),
            save_name=Dict.get('save_name', ''),
        )