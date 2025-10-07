#New game config
def start_game(conn, user_name: str, difficulty: str, airport_name: str):
    try:
        with conn.cursor() as cursor:
            #1 Check if the player already exists
            cursor.execute("SELECT id FROM player WHERE name = %s", (user_name,))
            row = cursor.fetchone()
            if row:
                player_id = row[0]
                return {"status": "exists", "player_id": player_id}

            #2 Create a new player
            cursor.execute("""
                INSERT INTO player (name, difficulty_level, battery_level, total_score, games_played, games_won, created_at)
                VALUES (%s, %s, 100, 0, 0, 0, NOW())
            """, (user_name, difficulty))
            player_id = cursor.lastrowid

            #3 Get the starting airport
            cursor.execute("SELECT id, country_code FROM airport WHERE name = %s", (airport_name,))
            start_airport = cursor.fetchone()
            if not start_airport:
                raise ValueError(f"Airport '{airport_name}' not found.")
            start_airport_id, start_country_code = start_airport

            #4 Update the player's current location
            cursor.execute("UPDATE player SET current_airport_id = %s WHERE id = %s", (start_airport_id, player_id))

            #5 Randomly select the boss airport and its country
            cursor.execute("SELECT id, country_code FROM airport ORDER BY RAND() LIMIT 1;")
            boss_airport_id, boss_country_code = cursor.fetchone()

            #6 Create a new game_session and save both boss airport and country code
            cursor.execute("""
                    INSERT INTO game_session (
                    player_id, difficulty_level,
                    starting_airport_id, current_airport_id,
                    boss_airport_id, boss_country_code,
                    status, started_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW())
            """, (player_id, difficulty, start_airport_id, start_airport_id, boss_airport_id, boss_country_code))
            session_id = cursor.lastrowid
            conn.commit()
            return {
                "status": "new_game",
                "player_id": player_id,
                "session_id": session_id,
                "starting_airport_id": start_airport_id,
                "boss_airport_id": boss_airport_id,
                "boss_country_code": boss_country_code
            }
    except Error as e:
        conn.rollback()
        return {"status": "error", "error": str(e)}

#check if player exists and has active status, Return boolean based on that
def load_game(conn, player_name: str) -> bool:
    try:
        with conn.cursor() as cursor:
            #1 Check if player exists
            cursor.execute("SELECT id FROM player WHERE name = %s", (player_name,))
            player = cursor.fetchone()
            if not player:
                return False
            player_id = player[0]

            #2 Check if player has an active game session
            cursor.execute("""
                SELECT id FROM game_session
                WHERE player_id = %s AND status = 'active'
                ORDER BY started_at DESC
                LIMIT 1
            """, (player_id,))
            session = cursor.fetchone()

            if not session:
                return False
            #3 Active game exists — can continue
            return True

    except Error as e:
        print("Database error:", e)
        return False

#Return all countries with airports in a list
def get_country_names():
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT DISTINCT country.name 
                FROM country
                JOIN airport ON country_code = code""")
        result = cursor.fetchall()
        return [row[0] for row in result]

#Return available airports based on country name
def get_airports(country_name:str):
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT airport.name
                FROM airport
                JOIN country ON country_code = code
                WHERE country.name = %s
                       """, (country_name,))
        result = cursor.fetchall()

        if result:
            #If country has aiports, return all of them in a list
            return [row[0] for row in result]
        else:
            #If not return none
            return None

import random

def get_challenge(self, player_difficulty: Difficulty):
    challenge_type = random.choice(["question_task", "multiple_choice"])

    if challenge_type == "question_task":
        result = self.execute_query(
            "SELECT question, correct_answer FROM question_task WHERE difficulty_level = %s ORDER BY RAND() LIMIT 1",
            (player_difficulty.value,)
        )
        if result:
            row = result[0]
            return OpenQuestion(
                question=row["question"],
                answer=row["correct_answer"]
            )
        return None

    else:
        question_result = self.execute_query(
            "SELECT id, question FROM multiple_choice_question WHERE difficulty_level = %s ORDER BY RAND() LIMIT 1",
            (player_difficulty.value,)
        )
        if not question_result:
            return None
        question = question_result[0]

        answers = self.execute_query(
            "SELECT answer, is_correct FROM multiple_choice_answer WHERE question_id = %s",
            (question["id"],)
        )
        if not answers:
            return None

        random.shuffle(answers)
        options = [
            MultipleChoiceOption(name=a["answer"], is_correct=a["is_correct"])
            for a in answers
        ]

        return MultipleChoiceQuestion(
            question=question["question"],
            options=options
        )
