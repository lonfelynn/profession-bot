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

            cur.execute("""
                CREATE TABLE IF NOT EXISTS professions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    interaction_level INTEGER CHECK (interaction_level BETWEEN 0 AND 2),
                    education_level INTEGER CHECK (education_level BETWEEN 0 AND 3)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS profession_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profession_id INTEGER,
                    category TEXT,
                    FOREIGN KEY (profession_id) REFERENCES professions(id)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS profession_requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profession_id INTEGER,
                    requirement TEXT,
                    FOREIGN KEY (profession_id) REFERENCES professions(id)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    profession_id INTEGER,
                    is_satisfied INTEGER CHECK (is_satisfied IN (0,1))
                );
            """)

    def get_all_categories(self):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT category
            FROM profession_categories
            ORDER BY category
        """)
        return [row[0] for row in cur.fetchall()]

    def get_all_requirements(self, category):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute("""
            SELECT requirement
            FROM profession_requirements
            WHERE profession_id IN (
                SELECT profession_id
                FROM profession_categories
                WHERE category = ?
            )
        """, (category,))
        return [row[0] for row in cur.fetchall()]

    def get_professions_in_category(self, category):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name
            FROM professions p
            JOIN profession_categories c ON p.id = c.profession_id
            WHERE c.category = ?
        """, (category,))
        return cur.fetchall()

    def get_profession_details(self, prof_id: int):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, description, interaction_level, education_level
            FROM professions
            WHERE id = ?
        """, (prof_id,))
        row = cur.fetchone()

        if not row:
            return None

        result = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "interaction_level": row[3],
            "education_level": row[4],
        }

        cur.execute("""
            SELECT category FROM profession_categories
            WHERE profession_id = ?
        """, (prof_id,))
        result["categories"] = [r[0] for r in cur.fetchall()]

        cur.execute("""
            SELECT requirement FROM profession_requirements
            WHERE profession_id = ?
        """, (prof_id,))
        result["requirements"] = [r[0] for r in cur.fetchall()]

        conn.close()
        return result

    
    def find_professions(self, interaction_level=None, category=None, requirement=None, education_max=None):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        query = """
            SELECT DISTINCT p.id, p.name, p.description
            FROM professions p
            LEFT JOIN profession_categories c ON p.id = c.profession_id
            LEFT JOIN profession_requirements r ON p.id = r.profession_id
            WHERE 1=1
        """
        params = []

        if interaction_level is not None:
            query += " AND p.interaction_level = ?"
            params.append(interaction_level)

        if category is not None:
            query += " AND c.category = ?"
            params.append(category)

        if requirement is not None:
            query += " AND r.requirement = ?"
            params.append(requirement)

        if education_max is not None:
            query += " AND p.education_level <= ?"
            params.append(education_max)

        cur.execute(query, params)
        return cur.fetchall()
    

    def add_user(self, user_id: int, name: str, age: int):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO users (id, name, age)
            VALUES (?, ?, ?)
        """, (user_id, name, age))

        conn.commit()
        conn.close()

    
    def save_user_feedback(self, user_id: int, profession_id: int, is_satisfied: int):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users_feedback (user_id, profession_id, is_satisfied)
            VALUES (?, ?, ?)
        """, (user_id, profession_id, is_satisfied))

        conn.commit()
        conn.close()


    