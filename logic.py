import sqlite3
from config import database

class DB_Manager:
    def __init__(self, database):
        self.database = database
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()

            #PROFESSIONS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS professions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    interaction_level INTEGER CHECK (interaction_level BETWEEN 0 AND 2),
                    education_level INTEGER CHECK (education_level BETWEEN 0 AND 3)
                );
            """)

            #CATEGORIES
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profession_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profession_id INTEGER,
                    category TEXT,
                    FOREIGN KEY (profession_id) REFERENCES professions(id)
                );
            """)

            #REQUIREMENTS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profession_requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profession_id INTEGER,
                    requirement TEXT,
                    FOREIGN KEY (profession_id) REFERENCES professions(id)
                );
            """)

            #USER FEEDBACK
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    profession_id INTEGER,
                    is_satisfied INTEGER CHECK (is_satisfied IN (0,1))
                );
            """)

            conn.commit()

if __name__ == '__main__':
    manager = DB_Manager(database)