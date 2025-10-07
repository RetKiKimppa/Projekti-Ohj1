from dataclasses import dataclass
from enum import Enum

class GameStatus(Enum):
    ACTIVE = 'active'
    WON = 'won'
    LOST = 'lost'
    ABANDONED = 'abandoned'

class Difficulty(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

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
        return cls(
            id=Dict.get('id', 0),
            icao_code=Dict.get('icao_code', ''),
            iata_code=Dict.get('iata_code', ''),
            name=Dict.get('name', ''),
            city=Dict.get('city', ''),
            country_code=Dict.get('country_code', ''),
            latitude=Dict.get('latitude', 0.0),
            longitude=Dict.get('longitude', 0.0),
            elevation_ft=Dict.get('elevation_ft', 0),
            continent=Dict.get('continent', '')
        )

@dataclass
class CountryDto:
    code: str
    name: str
    continent: str

    @classmethod
    def create(cls, Dict):
        return cls(
            code=Dict.get('code', ''),
            name=Dict.get('name', ''),
            continent=Dict.get('continent', '')
        )