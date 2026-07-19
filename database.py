"""
database.py — ניהול משתמשים ב-SQLite.

טבלת users:
    username    TEXT PRIMARY KEY
    password    TEXT (hashed)
    rating      INTEGER (starts at 1200, moves by ELO)

שימוש:
    db = Database()
    db.register("noa", "1234")       -> True/False
    db.login("noa", "1234")          -> True/False
    db.get_rating("noa")             -> 1200
    db.update_ratings("noa", "dan")  -> מעדכן ELO אחרי ניצחון של noa
"""
import sqlite3
import hashlib

DB_FILE = "kungfu_chess.db"
DEFAULT_RATING = 1200
ELO_K_FACTOR = 32  # כמה נקודות אפשר לזכות/להפסיד במשחק


class Database:
    def __init__(self, db_path=DB_FILE):
        self._conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        """יוצר את טבלת users אם לא קיימת."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 1200
            )
        """)
        self._conn.commit()

    def _hash_password(self, password: str) -> str:
        """ממיר סיסמה ל-hash (SHA256)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str) -> bool:
        """
        רושם משתמש חדש.
        מחזיר True אם הצליח, False אם השם כבר תפוס.
        """
        try:
            hashed = self._hash_password(password)
            self._conn.execute(
                "INSERT INTO users (username, password, rating) VALUES (?, ?, ?)",
                (username, hashed, DEFAULT_RATING)
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # username already exists

    def login(self, username: str, password: str) -> bool:
        """
        מאמת משתמש.
        מחזיר True אם הסיסמה נכונה, False אחרת.
        """
        hashed = self._hash_password(password)
        cursor = self._conn.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row is None:
            return False  # user doesn't exist
        return row[0] == hashed

    def user_exists(self, username: str) -> bool:
        """בודק אם משתמש קיים."""
        cursor = self._conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,)
        )
        return cursor.fetchone() is not None

    def get_rating(self, username: str) -> int:
        """מחזיר את הrating של משתמש."""
        cursor = self._conn.execute(
            "SELECT rating FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return row[0] if row else DEFAULT_RATING

    def update_ratings(self, winner: str, loser: str):
        """
        מעדכן ELO אחרי משחק.
        המנצח עולה, המפסיד יורד.
        """
        winner_rating = self.get_rating(winner)
        loser_rating = self.get_rating(loser)

        # חישוב ELO
        expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))

        new_winner_rating = round(winner_rating + ELO_K_FACTOR * (1 - expected_winner))
        new_loser_rating = round(loser_rating + ELO_K_FACTOR * (0 - expected_loser))

        self._conn.execute(
            "UPDATE users SET rating = ? WHERE username = ?",
            (new_winner_rating, winner)
        )
        self._conn.execute(
            "UPDATE users SET rating = ? WHERE username = ?",
            (new_loser_rating, loser)
        )
        self._conn.commit()

        return new_winner_rating, new_loser_rating

    def close(self):
        self._conn.close()
