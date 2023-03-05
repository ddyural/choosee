import sqlite3
import time

def init_db(force: bool=False):
	with sqlite3.connect("spis.db") as con:
		c = con.cursor()
		if force:
			c.execute("DROP TABLE IF EXISTS users")

		c.execute("""
			CREATE TABLE IF NOT EXISTS users (
				id                  INTEGER PRIMARY KEY,
				user_id             INTEGER NOT NULL,
				login               INTEGER NOT NULL,
				cookie              TEXT    NOT NULL,
				homeworktime        TEXT,
				fio                 TEXT    NOT NULL,
				school              TEXT    DEFAULT Ученик,
				users_class         TEXT    NOT NULL,
				term                TEXT,
				custom_titles       TEXT,
				send_changes        BOOLEAN,
				take_part_in_rating BOOLEAN
			);
		""")
		c.execute("""
			CREATE TABLE IF NOT EXISTS reminders (
			    id      INTEGER PRIMARY KEY,
			    user_id INTEGER,
			    content TEXT,
			    time    STRING,
			    date    STRING
			);

			""")
		con.commit()


def add_new_user(user_id, login, cookie, fio, users_class, term, custom_titles):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute(
				"""INSERT INTO
					users(user_id, login, cookie, fio, users_class, term, custom_titles, send_changes, take_part_in_rating)
					VALUES(?, ?, ?, ?, ?, ?, ?, true, false);""",
				(user_id, login, str(cookie), fio, users_class, term, custom_titles)
			)
		con.commit()

def change_homeworktime(user_id, homeworktime):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET homeworktime = ? WHERE user_id = ?;", (homeworktime, user_id))
		con.commit()

def get_profile(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT fio, users_class, login FROM users WHERE user_id = ?;", (user_id, ))

		fio, users_class, login = cur.fetchone()

		return fio, users_class, login

def delete_user(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("DELETE FROM users WHERE user_id = ?;", (user_id, ))
		con.commit()

def get_cookie_data(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT cookie FROM users WHERE user_id = ?;", (user_id, ))

		return cur.fetchone()

def check_user(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT id FROM users WHERE user_id = ?;", (user_id, ))
		res = cur.fetchall()

		return bool(res)

def get_homeworktime():
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT user_id, homeworktime FROM users;")
		
		return cur.fetchall()

def get_terms(users_class=None):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()
		if users_class:
			cur.execute("SELECT fio, term FROM users WHERE users_class = ? AND take_part_in_rating = true;", (users_class, ))
		else:
			cur.execute("SELECT user_id, term, send_changes FROM users;")

		return cur.fetchall()

def update_term(user_id, term):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET term = ? WHERE user_id = ?;", (term, user_id))
		con.commit()

def create_reminder(user_id, content, date, time):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute(
				"INSERT INTO reminders(user_id, content, date, time) VALUES(?, ?, ?, ?);",
				(user_id, content, date, time)
			)
		con.commit()

def get_reminders():
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT * FROM reminders;")

		return cur.fetchall()

def delete_reminder(user_id, date, time):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("DELETE FROM reminders WHERE user_id = ? AND date = ? AND time = ?;", (user_id, date, time))
		con.commit()

def get_items(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT custom_titles FROM users WHERE user_id = ?;", (user_id,))
		return cur.fetchone()

def update_items(user_id, customized_items):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET custom_titles = ? WHERE user_id = ?;", (customized_items, user_id))
		con.commit()

def get_send_changes(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT send_changes FROM users WHERE user_id = ?;", (user_id, ))
		return cur.fetchone()

def update_send_changes(user_id, state):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET send_changes = ? WHERE user_id = ?;", (state, user_id))
		con.commit()

def get_take_part_in_rating(user_id):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("SELECT take_part_in_rating FROM users WHERE user_id = ?;", (user_id, ))
		return cur.fetchone()

def update_take_part_in_rating(user_id, state):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET take_part_in_rating = ? WHERE user_id = ?;", (state, user_id))
		con.commit()

def update_cookie(user_id, cookie):
	with sqlite3.connect("spis.db") as con:
		cur = con.cursor()

		cur.execute("UPDATE users SET cookie = ? WHERE user_id = ?;", (cookie, user_id))
		con.commit()

if __name__ == "__main__":
	init_db()