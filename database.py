# database.py
import sqlite3
import datetime
import os

DB_NAME = 'rpg_life.db'

def get_db_connection():
    """Устанавливает соединение с БД."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Возвращает строки как словари
    return conn

def init_db():
    """Инициализирует таблицы в БД, если их нет."""
    if os.path.exists(DB_NAME):
        print("Database already exists.")
        # Возможно, здесь стоит добавить проверку и обновление схемы, если нужно
        # return

    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Таблица персонажа ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character (
            id INTEGER PRIMARY KEY CHECK (id = 1), -- Только один персонаж
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            xp_to_next_level INTEGER DEFAULT 100,
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            gold INTEGER DEFAULT 0
        )
    ''')
    # Вставляем персонажа, если его нет
    cursor.execute('''
        INSERT OR IGNORE INTO character (id) VALUES (1)
    ''')

    # --- Таблица привычек (Habits) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('+', '-', '+-')) NOT NULL, -- +, -, или +-
            value_xp INTEGER DEFAULT 5,
            value_gold INTEGER DEFAULT 1,
            value_dmg INTEGER DEFAULT 5, -- Урон для плохих привычек
            counter INTEGER DEFAULT 0,
            last_triggered_pos DATE, -- Дата последнего позитивного триггера
            last_triggered_neg DATE  -- Дата последнего негативного триггера
        )
    ''')

    # --- Таблица ежедневок (Dailies) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dailies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            frequency TEXT DEFAULT 'daily', -- 'daily', 'weekly:Mon', 'monthly:1' и т.д. (пока упростим до 'daily')
            completed_today BOOLEAN DEFAULT 0,
            last_completed DATE,
            streak INTEGER DEFAULT 0,
            value_xp INTEGER DEFAULT 10,
            value_gold INTEGER DEFAULT 5,
            penalty_hp INTEGER DEFAULT 10 -- Штраф за невыполнение
        )
    ''')

    # --- Таблица разовых задач (To-Dos) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT,
            due_date DATE,
            creation_date DATE DEFAULT CURRENT_DATE,
            completed BOOLEAN DEFAULT 0,
            value_xp INTEGER DEFAULT 20,
            value_gold INTEGER DEFAULT 10,
            difficulty INTEGER DEFAULT 1 -- Можно использовать для расчета ценности
        )
    ''')

    # --- Таблица наград/инвентаря (просто) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('equipment', 'pet', 'custom')) NOT NULL,
            description TEXT,
            cost INTEGER DEFAULT 0, -- Цена в золоте для покупки
            sprite_name TEXT, -- Имя файла спрайта в assets/
            owned BOOLEAN DEFAULT 0, -- Владеет ли игрок
            equipped BOOLEAN DEFAULT 0 -- Экипировано ли (если применимо)
        )
    ''')
    # Добавим примеры наград из спрайтов
    cursor.execute("INSERT OR IGNORE INTO rewards (name, type, cost, sprite_name) VALUES (?, ?, ?, ?)",
                   ('Боевой Топор', 'equipment', 50, 'axe.png'))
    cursor.execute("INSERT OR IGNORE INTO rewards (name, type, cost, sprite_name) VALUES (?, ?, ?, ?)",
                   ('Маленький Дракон', 'pet', 100, 'dragon.png'))
    cursor.execute("INSERT OR IGNORE INTO rewards (name, type, cost, sprite_name) VALUES (?, ?, ?, ?)",
                   ('Легкое Перо', 'custom', 10, 'feather.png')) # 'custom' - для пользовательских наград
    cursor.execute("INSERT OR IGNORE INTO rewards (name, type, cost, sprite_name) VALUES (?, ?, ?, ?)",
                   ('Магический Фамильяр', 'pet', 75, 'creature.png'))

    conn.commit()
    conn.close()
    print("Database initialized.")

# --- Функции для получения/обновления данных ---

def get_character_data():
    conn = get_db_connection()
    char = conn.execute('SELECT * FROM character WHERE id = 1').fetchone()
    conn.close()
    return dict(char) if char else None

def update_character_data(data):
    conn = get_db_connection()
    conn.execute('''
        UPDATE character SET
            level = ?, xp = ?, xp_to_next_level = ?, health = ?, max_health = ?, gold = ?
        WHERE id = 1
    ''', (data['level'], data['xp'], data['xp_to_next_level'], data['health'], data['max_health'], data['gold']))
    conn.commit()
    conn.close()

# --- Функции для Задач (CRUD - Create, Read, Update, Delete) ---

def get_tasks(task_type):
    """Получает все задачи указанного типа ('habits', 'dailies', 'todos')."""
    conn = get_db_connection()
    if task_type == 'todos':
        # Показываем невыполненные тудушки
        tasks = conn.execute(f'SELECT * FROM {task_type} WHERE completed = 0 ORDER BY creation_date').fetchall()
    else:
        tasks = conn.execute(f'SELECT * FROM {task_type} ORDER BY id').fetchall()
    conn.close()
    return [dict(task) for task in tasks]

def add_task(task_type, data):
    """Добавляет новую задачу."""
    conn = get_db_connection()
    if task_type == 'habits':
        cursor = conn.execute(
            'INSERT INTO habits (name, type, value_xp, value_gold, value_dmg) VALUES (?, ?, ?, ?, ?)',
            (data['name'], data.get('type', '+-'), data.get('value_xp', 5), data.get('value_gold', 1), data.get('value_dmg', 5))
        )
    elif task_type == 'dailies':
         cursor = conn.execute(
            'INSERT INTO dailies (name, frequency, value_xp, value_gold, penalty_hp) VALUES (?, ?, ?, ?, ?)',
            (data['name'], data.get('frequency', 'daily'), data.get('value_xp', 10), data.get('value_gold', 5), data.get('penalty_hp', 10))
        )
    elif task_type == 'todos':
         cursor = conn.execute(
            'INSERT INTO todos (name, notes, due_date, value_xp, value_gold, difficulty) VALUES (?, ?, ?, ?, ?, ?)',
            (data['name'], data.get('notes'), data.get('due_date'), data.get('value_xp', 20), data.get('value_gold', 10), data.get('difficulty', 1))
        )
    else:
        conn.close()
        return None
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_task(task_type, task_id, updates):
    """Обновляет задачу (например, отметка о выполнении)."""
    conn = get_db_connection()
    # Строим строку SET динамически (будьте осторожны с SQL инъекциями, если данные от пользователя!)
    set_clause = ", ".join([f"{key} = ?" for key in updates])
    values = list(updates.values())
    values.append(task_id)

    try:
        conn.execute(f'UPDATE {task_type} SET {set_clause} WHERE id = ?', tuple(values))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating task: {e}")
    finally:
        conn.close()

def delete_task(task_type, task_id):
    conn = get_db_connection()
    conn.execute(f'DELETE FROM {task_type} WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

# --- Функции для Наград ---
def get_rewards(owned_only=False):
    conn = get_db_connection()
    query = 'SELECT * FROM rewards'
    if owned_only:
        query += ' WHERE owned = 1'
    rewards = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rewards]

def update_reward(reward_id, updates):
     conn = get_db_connection()
     set_clause = ", ".join([f"{key} = ?" for key in updates])
     values = list(updates.values())
     values.append(reward_id)
     conn.execute(f'UPDATE rewards SET {set_clause} WHERE id = ?', tuple(values))
     conn.commit()
     conn.close()


# --- Функции для ежедневного сброса и проверки ---
def daily_reset():
    """Сбрасывает статус 'completed_today' для дейликов и начисляет штрафы."""
    conn = get_db_connection()
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    character_data = dict(conn.execute('SELECT health, max_health FROM character WHERE id = 1').fetchone())
    health_lost = 0

    # Проверяем вчерашние дейлики
    dailies_to_check = conn.execute('SELECT id, completed_today, last_completed, penalty_hp, streak FROM dailies').fetchall()

    for daily in dailies_to_check:
        daily_dict = dict(daily)
        last_comp_date = None
        if daily_dict['last_completed']:
            last_comp_date = datetime.datetime.strptime(daily_dict['last_completed'], '%Y-%m-%d').date()

        # Если дейлик не был выполнен вчера (или никогда) и должен был быть
        # Упрощение: пока считаем все дейлики ежедневными
        # TODO: Добавить логику для frequency
        if last_comp_date != today: # Если сегодня еще не выполнен
             # Если вчера не был выполнен или был пропущен день
            if not daily_dict['completed_today'] or (last_comp_date and last_comp_date < yesterday):
                 # Штраф!
                 health_lost += daily_dict['penalty_hp']
                 # Сброс стрика
                 conn.execute('UPDATE dailies SET streak = 0 WHERE id = ?', (daily_dict['id'],))
                 print(f"Daily '{daily_dict['id']}' missed. Penalty: {daily_dict['penalty_hp']} HP. Streak reset.")
            elif daily_dict['completed_today'] and last_comp_date == yesterday:
                 # Был выполнен вчера, сегодня сбрасываем для нового выполнения
                 pass # Стрик сохраняется

            # Сбрасываем флаг выполнения на сегодня
            conn.execute('UPDATE dailies SET completed_today = 0 WHERE id = ?', (daily_dict['id'],))


    if health_lost > 0:
        new_health = max(0, character_data['health'] - health_lost)
        conn.execute('UPDATE character SET health = ? WHERE id = 1', (new_health,))
        print(f"Total health lost from missed dailies: {health_lost}. New health: {new_health}")

    conn.commit()
    conn.close()

def check_last_run_date():
    """Проверяет, запускалось ли приложение сегодня. Если нет, выполняет daily_reset."""
    filepath = '.last_run_date'
    today_str = str(datetime.date.today())
    try:
        with open(filepath, 'r') as f:
            last_run_date_str = f.read().strip()
    except FileNotFoundError:
        last_run_date_str = ''

    if last_run_date_str != today_str:
        print("First run of the day or missed days. Running daily reset...")
        daily_reset()
        with open(filepath, 'w') as f:
            f.write(today_str)
        print("Daily reset complete.")
    else:
        print("Already ran today.")

if __name__ == '__main__':
    # Этот блок выполнится, только если запустить database.py напрямую
    # Используется для первоначальной инициализации БД
    print("Initializing database...")
    init_db()
    print("--- Initial Character Data ---")
    print(get_character_data())
    print("--- Initial Rewards ---")
    print(get_rewards())