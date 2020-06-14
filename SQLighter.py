import sqlite3
from time import time as TIME


class SQLighter:

    def __init__(self, database):
        """Подключение к БД и сохраненние курсора соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def is_user_in_base(self, user_id):
        """Проверка, есть ли юзер в БД"""
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM config WHERE user_id = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id):
        """Добавление юзера в БД"""
        with self.connection:
            return self.cursor.execute("INSERT INTO config VALUES(?,25,5,50,10)", (user_id,))

    def drop_user(self, user_id):
        """Удаление юзера из БД"""
        with self.connection:
            return self.cursor.execute("DELETE FROM config WHERE user_id = ?", (user_id,))

    def set_config(self, user_id, w_time, r_time, w2_time, r2_time):
        """Установка времени стандартных таймеров"""
        if not self.is_user_in_base(user_id):
            self.add_user(user_id)
        with self.connection:
            return self.cursor.execute(
                "UPDATE config SET w_time = ?, r_time = ?, w2_time = ?, r2_time = ? WHERE user_id = ?",
                (w_time, r_time, w2_time, r2_time, user_id))

    def get_config(self, user_id):
        """Получение установленного времени стандартных таймеров"""
        if not self.is_user_in_base(user_id):
            self.add_user(user_id)
        with self.connection:
            return self.cursor.execute(
                "SELECT w_time, r_time, w2_time, r2_time FROM config WHERE user_id = ?", (user_id,)).fetchone()

    def set_timer(self, user_id, min_dur, mode):
        """Установка таймера"""
        with self.connection:
            self.cursor.execute("DELETE FROM timers_on WHERE user_id = ?", (user_id,))
            return self.cursor.execute("INSERT INTO timers_on VALUES(?,?,?,?)",
                                       (user_id, TIME() + min_dur * 60, min_dur, mode))

    def give_points_and_del_timer(self, user_id, points, mode):
        """Начисление таймреа в статистику и удаление"""
        with self.connection:
            if not self.cursor.execute("SELECT * FROM stats WHERE user_id = ?", (user_id,)).fetchone():
                self.cursor.execute("INSERT INTO stats VALUES(?,0,0,0,0)", (user_id,))
            if mode in ['w', 'W']:
                self.cursor.execute("UPDATE stats SET w_timers = w_timers + 1, w_mins = w_mins + ? WHERE user_id = ?",
                                    (points, user_id))
            else:
                self.cursor.execute("UPDATE stats SET r_timers = r_timers + 1, r_mins = r_mins + ? WHERE user_id = ?",
                                    (points, user_id))
            return self.cursor.execute("DELETE FROM timers_on WHERE user_id = ?", (user_id,))

    def del_timer(self, user_id):
        """Удаление таймера"""
        with self.connection:
            return self.cursor.execute("DELETE FROM timers_on WHERE user_id = ?", (user_id,))

    def get_timer(self, user_id):
        """Получение установленного времени таймера"""
        with self.connection:
            result = self.cursor.execute("SELECT f_time FROM timers_on WHERE user_id = ?", (user_id,)).fetchone()
            if result:
                result = result[0]
            return result

    def get_mode_from_timers_on(self, user_id):
        """Получение режима заведенного таймера"""
        with self.connection:
            result = self.cursor.execute("SELECT mode FROM timers_on WHERE user_id = ?", (user_id,)).fetchone()
            if result:
                result = result[0]
            return result

    def check_timers(self):
        """Проверка на законченные таймеры"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM timers_on WHERE f_time = (SELECT MIN(f_time) FROM timers_on)").fetchone()
            if result:
                user_id, f_time, points, mode = result
                if TIME() >= f_time:
                    return user_id, points, mode

    def pause_timer(self, user_id):
        """Приостановка таймера"""
        with self.connection:
            points, mode = self.cursor.execute("SELECT points, mode FROM timers_on WHERE user_id = ?",
                                               (user_id,)).fetchone()
            self.cursor.execute("DELETE FROM timers_off WHERE user_id = ?", (user_id,))
            self.cursor.execute("INSERT INTO timers_off VALUES(?,?,?,?)",
                                (user_id, self.get_timer(user_id) - TIME(), points, mode))
            self.cursor.execute("DELETE FROM timers_on WHERE user_id = ?", (user_id,))
            return mode

    def resume_timer(self, user_id):
        """Возобновление таймера"""
        with self.connection:
            duration = self.cursor.execute("SELECT duration FROM timers_off WHERE user_id = ?", (user_id,)).fetchone()
            if duration:
                duration = duration[0]
                points, mode = self.cursor.execute("SELECT points, mode FROM timers_off WHERE user_id = ?",
                                                   (user_id,)).fetchone()
                self.cursor.execute("DELETE FROM timers_on WHERE user_id = ?", (user_id,))
                self.cursor.execute("INSERT INTO timers_on VALUES(?,?,?,?)", (user_id, TIME() + duration, points, mode))
                self.cursor.execute("DELETE FROM timers_off WHERE user_id = ?", (user_id,))
                return duration

    def get_stats(self, user_id):
        """Получение статистики"""
        with self.connection:
            return self.cursor.execute("SELECT w_timers, r_timers, w_mins, r_mins FROM stats WHERE user_id = ?",
                                       (user_id,)).fetchone()

    def update_stats(self, user_id):
        """Обнуление статистики по айди"""
        with self.connection:
            return self.cursor.execute(
                "UPDATE stats SET w_timers = 0, r_timers = 0, w_mins = 0, r_mins = 0 WHERE user_id = ?", (user_id,))

    def close(self):
        """Закрытие соединение с БД"""
        self.connection.close()
