# main.py
import pygame
import sys
import os
import datetime
from database import (
    init_db, get_db_connection, get_character_data, update_character_data,
    get_tasks, add_task, update_task, delete_task,
    get_rewards, update_reward, check_last_run_date
)

# --- Константы ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255) # Используемый синий фон
GOLD_COLOR = (255, 215, 0)
XP_COLOR = (150, 150, 255)
HEALTH_COLOR = (255, 100, 100)

ASSETS_FOLDER = 'assets'
DEFAULT_BG_COLOR = (40, 120, 190) # Примерно синий цвет фона


INPUT_BOX_COLOR = (230, 230, 230)
INPUT_BOX_BORDER_COLOR = BLACK
INPUT_TEXT_COLOR = BLACK
INPUT_ACTIVE_BORDER_COLOR = BLUE


# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RPG Life Tracker")
clock = pygame.time.Clock()
FONT_SMALL = pygame.font.SysFont(None, 24)
FONT_MEDIUM = pygame.font.SysFont(None, 36)
FONT_LARGE = pygame.font.SysFont(None, 48)

# --- Загрузка спрайтов ---
def load_sprite(name, size=None):
    """Загружает спрайт из папки assets."""
    path = os.path.join(ASSETS_FOLDER, name)
    try:
        image = pygame.image.load(path).convert_alpha()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except pygame.error as e:
        print(f"Cannot load image: {name} - {e}")
        # Возвращаем заглушку
        fallback = pygame.Surface(size if size else (32, 32))
        fallback.fill(RED)
        return fallback

SPRITES = {
    'checkmark': load_sprite('checkmark.png', (24, 24)),
    'x_button': load_sprite('x_button.png', (24, 24)),
    'character': load_sprite('character.png', (64, 64)),
    'background_tile': load_sprite('background.png'), # Пиксельный фон
    # Добавим спрайты наград
    'axe': load_sprite('axe.png', (32, 32)),
    'dragon': load_sprite('dragon.png', (32, 32)),
    'feather': load_sprite('feather.png', (32, 32)),
    'creature': load_sprite('creature.png', (32, 32)),
    'map_study': load_sprite('map_study.png', (32, 32)),
}
# Создаем тайловый фон, если спрайт загрузился
BG_SURFACE = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
if SPRITES['background_tile'].get_width() > 1: # Проверка что не заглушка
    bw, bh = SPRITES['background_tile'].get_size()
    for y in range(0, SCREEN_HEIGHT, bh):
        for x in range(0, SCREEN_WIDTH, bw):
            BG_SURFACE.blit(SPRITES['background_tile'], (x, y))
else:
    BG_SURFACE.fill(DEFAULT_BG_COLOR) # Используем сплошной цвет, если фона нет

# --- Вспомогательные функции ---
def draw_text(surface, text, font, color, rect, aa=True, bkg=None):
    """Отрисовывает текст с выравниванием по центру прямоугольника."""
    y = rect.top
    lineSpacing = -2

    # Получаем высоту шрифта
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1
        # Определяем, сколько текста помещается в строку
        if y + fontHeight > rect.bottom:
            break
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1
        # Если текст не поместился, ищем последний пробел
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1
        if i == 0: # Если слово слишком длинное
            i = 1 # Рисуем по одной букве, чтобы избежать бесконечного цикла

        # Отрисовываем строку
        image = font.render(text[:i], aa, color, bkg)
        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # Убираем отрисованную часть текста
        text = text[i:]

    return text

def draw_progress_bar(surface, x, y, w, h, current, maximum, color, label=""):
    """Рисует полосу прогресса."""
    if maximum == 0: maximum = 1 # Избегаем деления на ноль
    fill_ratio = max(0, min(1, current / maximum))
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h))
    pygame.draw.rect(surface, color, (x, y, int(w * fill_ratio), h))
    pygame.draw.rect(surface, BLACK, (x, y, w, h), 1) # Обводка
    bar_text = f"{label}{int(current)} / {int(maximum)}"
    text_surf = FONT_SMALL.render(bar_text, True, WHITE)
    text_rect = text_surf.get_rect(center=(x + w / 2, y + h / 2))
    surface.blit(text_surf, text_rect)

def draw_input_popup(surface, mode, input_data, active_field):
    """Рисует всплывающее окно для ввода данных задачи."""
    popup_width = 400
    popup_height = 250 # Может меняться в зависимости от полей
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    pygame.draw.rect(surface, INPUT_BOX_COLOR, popup_rect, border_radius=10)
    pygame.draw.rect(surface, INPUT_BOX_BORDER_COLOR, popup_rect, 2, border_radius=10)

    title = f"Add New {mode.capitalize()}"
    title_surf = FONT_MEDIUM.render(title, True, BLACK)
    surface.blit(title_surf, (popup_x + 15, popup_y + 15))

    field_y = popup_y + 60
    field_height = 30
    label_width = 80
    input_width = popup_width - label_width - 40 # Отступы слева/справа
    click_areas = {} # Словарь для кнопок и полей ввода { 'field_name': rect, 'save': rect, 'cancel': rect }

    fields_to_draw = []
    if mode == 'Habit':
        fields_to_draw = [('name', 'Name:'), ('type', 'Type (+/-/+-):')]
        # Можно добавить поля для XP/Gold/Dmg позже
    elif mode == 'Daily':
        fields_to_draw = [('name', 'Name:')]
        # Можно добавить Frequency, XP/Gold/Penalty позже
    elif mode == 'To-Do':
        fields_to_draw = [('name', 'Name:'), ('notes', 'Notes (opt):')]
        # Можно добавить Due Date, XP/Gold/Difficulty позже

    for field_key, label_text in fields_to_draw:
        # Метка
        label_surf = FONT_SMALL.render(label_text, True, BLACK)
        surface.blit(label_surf, (popup_x + 15, field_y + 5))

        # Поле ввода
        input_rect = pygame.Rect(popup_x + label_width + 15, field_y, input_width, field_height)
        border_color = INPUT_ACTIVE_BORDER_COLOR if active_field == field_key else INPUT_BOX_BORDER_COLOR
        pygame.draw.rect(surface, WHITE, input_rect)
        pygame.draw.rect(surface, border_color, input_rect, 1)
        click_areas[field_key] = input_rect # Добавляем поле для клика

        # Текст внутри поля
        text_surf = FONT_SMALL.render(input_data.get(field_key, ''), True, INPUT_TEXT_COLOR)
        surface.blit(text_surf, (input_rect.x + 5, input_rect.y + 5))

        # Курсор (простой)
        if active_field == field_key:
            cursor_x = input_rect.x + 5 + text_surf.get_width()
            if pygame.time.get_ticks() % 1000 < 500: # Мигание
                 pygame.draw.line(surface, BLACK, (cursor_x, input_rect.y + 5), (cursor_x, input_rect.y + field_height - 5), 1)


        field_y += field_height + 10

    # Кнопки Сохранить и Отмена
    button_width = 100
    button_height = 30
    save_rect = pygame.Rect(popup_x + popup_width // 2 - button_width - 10, field_y + 20, button_width, button_height)
    cancel_rect = pygame.Rect(popup_x + popup_width // 2 + 10, field_y + 20, button_width, button_height)

    pygame.draw.rect(surface, GREEN, save_rect, border_radius=5)
    pygame.draw.rect(surface, RED, cancel_rect, border_radius=5)

    save_text = FONT_SMALL.render("Save", True, WHITE)
    cancel_text = FONT_SMALL.render("Cancel", True, WHITE)
    surface.blit(save_text, save_text.get_rect(center=save_rect.center))
    surface.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

    click_areas['save'] = save_rect
    click_areas['cancel'] = cancel_rect

    # Динамически изменяем высоту окна, если нужно
    actual_height = (field_y + 20 + button_height + 15) - popup_y
    if actual_height != popup_height:
        popup_rect.height = actual_height
        # Перерисовываем фон и рамку с новой высотой
        pygame.draw.rect(surface, INPUT_BOX_COLOR, popup_rect, border_radius=10)
        pygame.draw.rect(surface, INPUT_BOX_BORDER_COLOR, popup_rect, 2, border_radius=10)
        # Придется перерисовать все элементы внутри, если высота изменилась значительно
        # В данном случае, кнопки просто сдвинутся ниже, так что перерисовка не строго обязательна
        # но для чистоты можно было бы перенести отрисовку кнопок после расчета высоты

    return click_areas, popup_rect # Возвращаем области клика и сам прямоугольник попапа



# --- Основные игровые функции ---
def gain_xp_gold(character, xp_gain, gold_gain):
    """Начисляет опыт и золото, проверяет левел-ап."""
    character['xp'] += xp_gain
    character['gold'] += gold_gain
    print(f"Gained {xp_gain} XP, {gold_gain} Gold.")

    while character['xp'] >= character['xp_to_next_level']:
        character['xp'] -= character['xp_to_next_level']
        character['level'] += 1
        # Увеличиваем здоровье и порог опыта
        character['max_health'] += 20
        character['health'] = character['max_health'] # Полное восстановление при левел-апе
        character['xp_to_next_level'] = int(character['xp_to_next_level'] * 1.5) # Усложняем следующий уровень
        print(f"LEVEL UP! Reached Level {character['level']}!")
        # Можно добавить звук или визуальный эффект

def lose_health(character, hp_loss):
    """Отнимает здоровье."""
    character['health'] = max(0, character['health'] - hp_loss)
    print(f"Lost {hp_loss} Health. Current: {character['health']}")
    # Что происходит при 0 HP? Может быть, дебафф или временная блокировка наград? Пока просто 0.

# МОДИФИЦИРУЕМ draw_task_list, чтобы добавить кнопку "+"
def draw_task_list(surface, title, tasks, task_type, x, y, w, h):
    """Рисует список задач и кнопку добавления."""
    base_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, GRAY, base_rect, border_radius=5)
    pygame.draw.rect(surface, BLACK, base_rect, 1, border_radius=5)

    title_surf = FONT_MEDIUM.render(title, True, BLACK)
    title_rect = title_surf.get_rect(topleft=(x + 10, y + 5))
    surface.blit(title_surf, title_rect)

    # Кнопка добавления (+)
    add_button_size = 24
    add_button_rect = pygame.Rect(x + w - add_button_size - 10, y + 5 + (title_rect.height - add_button_size)//2, add_button_size, add_button_size)
    pygame.draw.rect(surface, GREEN, add_button_rect, border_radius=5)
    add_text = FONT_LARGE.render("+", True, WHITE)
    surface.blit(add_text, add_text.get_rect(center=add_button_rect.center))

    item_y = y + 40
    item_height = 35
    button_size = 24
    click_areas = [] # Список для хранения [(rect, type, task_id, action), ...]
    # Добавляем кнопку "+" в кликабельные зоны
    click_areas.append((add_button_rect, task_type, None, 'add_new')) # task_id=None для кнопки добавления

    for task in tasks:
        if item_y + item_height > y + h - 10: break # Не выходим за границы

        task_rect = pygame.Rect(x + 5, item_y, w - 10, item_height)
        # ... (остальная отрисовка задачи как раньше) ...
        pygame.draw.rect(surface, WHITE, task_rect, border_radius=3)
        pygame.draw.rect(surface, DARK_GRAY, task_rect, 1, border_radius=3)

        task_name_rect = pygame.Rect(task_rect.left + 5, task_rect.top + 5, task_rect.width - 70, task_rect.height - 10)
        draw_text(surface, task['name'], FONT_SMALL, BLACK, task_name_rect)

        if task_type == 'habits':
            plus_rect = pygame.Rect(task_rect.right - button_size*2 - 10, task_rect.centery - button_size // 2, button_size, button_size)
            pygame.draw.rect(surface, GREEN, plus_rect, border_radius=3)
            plus_text = FONT_MEDIUM.render("+", True, WHITE)
            surface.blit(plus_text, plus_text.get_rect(center=plus_rect.center))
            click_areas.append((plus_rect, task_type, task['id'], 'positive'))
            if task['type'] in ('-', '+-'):
                minus_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
                pygame.draw.rect(surface, RED, minus_rect, border_radius=3)
                minus_text = FONT_MEDIUM.render("-", True, WHITE)
                surface.blit(minus_text, minus_text.get_rect(center=minus_rect.center))
                click_areas.append((minus_rect, task_type, task['id'], 'negative'))

        elif task_type == 'dailies':
            check_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
            if task['completed_today']:
                pygame.draw.rect(surface, DARK_GRAY, check_rect, border_radius=3)
                surface.blit(SPRITES['checkmark'], check_rect.topleft)
            else:
                pygame.draw.rect(surface, GREEN, check_rect, border_radius=3)
                surface.blit(SPRITES['checkmark'], check_rect.topleft)
                click_areas.append((check_rect, task_type, task['id'], 'complete'))
            streak_text = f"Streak: {task.get('streak', 0)}"
            streak_surf = FONT_SMALL.render(streak_text, True, BLUE)
            surface.blit(streak_surf, (task_rect.left + 5, task_rect.bottom - 15))

        elif task_type == 'todos':
            check_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
            pygame.draw.rect(surface, GREEN, check_rect, border_radius=3)
            surface.blit(SPRITES['checkmark'], check_rect.topleft)
            click_areas.append((check_rect, task_type, task['id'], 'complete'))

        item_y += item_height + 5

    return click_areas


# --- Функции отрисовки UI ---
def draw_character_panel(surface, char_data):
    """Рисует панель с информацией о персонаже."""
    panel_rect = pygame.Rect(10, 10, 300, 120)
    pygame.draw.rect(surface, GRAY, panel_rect, border_radius=10)
    pygame.draw.rect(surface, BLACK, panel_rect, 2, border_radius=10)

    # Аватар
    surface.blit(SPRITES['character'], (panel_rect.left + 10, panel_rect.top + 10))

    # Статы
    lvl_text = f"Level: {char_data['level']}"
    gold_text = f"Gold: {char_data['gold']}"

    lvl_surf = FONT_MEDIUM.render(lvl_text, True, BLACK)
    gold_surf = FONT_MEDIUM.render(gold_text, True, GOLD_COLOR)

    surface.blit(lvl_surf, (panel_rect.left + 80, panel_rect.top + 10))
    surface.blit(gold_surf, (panel_rect.left + 80, panel_rect.top + 40))

    # Бары
    bar_x = panel_rect.left + 10
    bar_width = panel_rect.width - 20
    draw_progress_bar(surface, bar_x, panel_rect.top + 70, bar_width, 15,
                       char_data['health'], char_data['max_health'], HEALTH_COLOR, "HP: ")
    draw_progress_bar(surface, bar_x, panel_rect.top + 90, bar_width, 15,
                       char_data['xp'], char_data['xp_to_next_level'], XP_COLOR, "XP: ")

# def draw_task_list(surface, title, tasks, task_type, x, y, w, h):
#     """Рисует список задач (Habits, Dailies, To-Dos)."""
#     base_rect = pygame.Rect(x, y, w, h)
#     pygame.draw.rect(surface, GRAY, base_rect, border_radius=5)
#     pygame.draw.rect(surface, BLACK, base_rect, 1, border_radius=5)

#     title_surf = FONT_MEDIUM.render(title, True, BLACK)
#     surface.blit(title_surf, (x + 10, y + 5))

#     item_y = y + 40
#     item_height = 35
#     button_size = 24
#     click_areas = [] # Список для хранения [(rect, type, task_id, action), ...]

#     for task in tasks:
#         if item_y + item_height > y + h - 10: break # Не выходим за границы

#         task_rect = pygame.Rect(x + 5, item_y, w - 10, item_height)
#         pygame.draw.rect(surface, WHITE, task_rect, border_radius=3)
#         pygame.draw.rect(surface, DARK_GRAY, task_rect, 1, border_radius=3)

#         # Название задачи
#         task_name_rect = pygame.Rect(task_rect.left + 5, task_rect.top + 5, task_rect.width - 70, task_rect.height - 10)
#         draw_text(surface, task['name'], FONT_SMALL, BLACK, task_name_rect)

#         # Кнопки действий
#         if task_type == 'habits':
#             # Кнопка "+"
#             plus_rect = pygame.Rect(task_rect.right - button_size*2 - 10, task_rect.centery - button_size // 2, button_size, button_size)
#             pygame.draw.rect(surface, GREEN, plus_rect, border_radius=3)
#             plus_text = FONT_MEDIUM.render("+", True, WHITE)
#             surface.blit(plus_text, plus_text.get_rect(center=plus_rect.center))
#             click_areas.append((plus_rect, task_type, task['id'], 'positive'))

#             # Кнопка "-" (если тип '-' или '+-')
#             if task['type'] in ('-', '+-'):
#                 minus_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
#                 pygame.draw.rect(surface, RED, minus_rect, border_radius=3)
#                 minus_text = FONT_MEDIUM.render("-", True, WHITE)
#                 surface.blit(minus_text, minus_text.get_rect(center=minus_rect.center))
#                 click_areas.append((minus_rect, task_type, task['id'], 'negative'))

#         elif task_type == 'dailies':
#             check_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
#             if task['completed_today']:
#                 pygame.draw.rect(surface, DARK_GRAY, check_rect, border_radius=3) # Отмечаем серым выполненные
#                 surface.blit(SPRITES['checkmark'], check_rect.topleft)
#             else:
#                 pygame.draw.rect(surface, GREEN, check_rect, border_radius=3) # Зеленая кнопка для выполнения
#                 surface.blit(SPRITES['checkmark'], check_rect.topleft)
#                 click_areas.append((check_rect, task_type, task['id'], 'complete'))
#             # Отображение стрика
#             streak_text = f"Streak: {task.get('streak', 0)}"
#             streak_surf = FONT_SMALL.render(streak_text, True, BLUE)
#             surface.blit(streak_surf, (task_rect.left + 5, task_rect.bottom - 15))


#         elif task_type == 'todos':
#             check_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
#             pygame.draw.rect(surface, GREEN, check_rect, border_radius=3)
#             surface.blit(SPRITES['checkmark'], check_rect.topleft)
#             click_areas.append((check_rect, task_type, task['id'], 'complete'))
#             # Можно добавить дату или сложность

#         item_y += item_height + 5

#     return click_areas # Возвращаем области, на которые можно кликнуть

def draw_rewards_panel(surface, rewards, character_gold, x, y, w, h):
    """Рисует панель с наградами."""
    base_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, GRAY, base_rect, border_radius=5)
    pygame.draw.rect(surface, BLACK, base_rect, 1, border_radius=5)

    title_surf = FONT_MEDIUM.render("Rewards Shop / Inventory", True, BLACK)
    surface.blit(title_surf, (x + 10, y + 5))

    item_y = y + 40
    item_height = 40
    button_size = 60
    click_areas = []

    for reward in rewards:
        if item_y + item_height > y + h - 10: break

        reward_rect = pygame.Rect(x + 5, item_y, w - 10, item_height)
        item_color = WHITE if not reward['owned'] else (220, 255, 220) # Светло-зеленый для купленных
        pygame.draw.rect(surface, item_color, reward_rect, border_radius=3)
        pygame.draw.rect(surface, DARK_GRAY, reward_rect, 1, border_radius=3)

        # Спрайт награды
        sprite_name = reward.get('sprite_name')
        if sprite_name and sprite_name in SPRITES:
            surface.blit(SPRITES[sprite_name.split('.')[0]], (reward_rect.left + 5, reward_rect.top + (item_height - 32)//2))
            text_x_offset = 45
        else:
            text_x_offset = 5

        # Название и тип
        name_surf = FONT_SMALL.render(f"{reward['name']} ({reward['type']})", True, BLACK)
        surface.blit(name_surf, (reward_rect.left + text_x_offset, reward_rect.top + 5))

        # Кнопка / Статус
        action_rect = pygame.Rect(reward_rect.right - button_size - 10, reward_rect.top + 5, button_size, item_height - 10)

        if reward['owned']:
            # Если предмет есть, показываем статус (или кнопку Equip)
            status_text = "Owned"
            if reward['type'] in ('equipment', 'pet') and reward.get('equipped'):
                 status_text = "Equipped"
                 pygame.draw.rect(surface, DARK_GRAY, action_rect, border_radius=3)
                 # TODO: Добавить кнопку Unequip?
            elif reward['type'] in ('equipment', 'pet'):
                 status_text = "Equip" # Можно сделать кнопкой
                 pygame.draw.rect(surface, BLUE, action_rect, border_radius=3)
                 click_areas.append((action_rect, 'reward', reward['id'], 'equip'))
            else: # Custom reward - просто owned
                pygame.draw.rect(surface, DARK_GRAY, action_rect, border_radius=3)

            status_surf = FONT_SMALL.render(status_text, True, WHITE if status_text=="Equip" else BLACK)
            surface.blit(status_surf, status_surf.get_rect(center=action_rect.center))

        else:
            # Если нет, показываем цену и кнопку Buy
            cost_text = f"{reward['cost']} G"
            can_afford = character_gold >= reward['cost']
            button_color = GOLD_COLOR if can_afford else DARK_GRAY
            pygame.draw.rect(surface, button_color, action_rect, border_radius=3)
            cost_surf = FONT_SMALL.render(cost_text, True, BLACK)
            surface.blit(cost_surf, cost_surf.get_rect(center=action_rect.center))
            if can_afford:
                click_areas.append((action_rect, 'reward', reward['id'], 'buy'))

        item_y += item_height + 5

    return click_areas

# --- Основной игровой цикл ---
def game_loop():
    """Главный цикл игры."""
    init_db()
    check_last_run_date()

    character_data = get_character_data()
    if not character_data:
        print("Error: Could not load character data!")
        sys.exit()

    habits = get_tasks('habits')
    dailies = get_tasks('dailies')
    todos = get_tasks('todos')
    rewards = get_rewards()

    running = True
    input_mode = None
    input_data = {}
    active_input_field = None

    # --- Переменные для хранения кликабельных зон ---
    # Они будут обновляться в конце каждого кадра (в секции отрисовки)
    # и использоваться в начале следующего кадра (в секции обработки событий)
    last_frame_main_ui_areas = []
    last_frame_popup_areas = {}
    last_frame_popup_rect = None

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # ===================================
        # === 1. ОБРАБОТКА СОБЫТИЙ / ВВОДА ===
        # ===================================
        # Используем области, сгенерированные на *предыдущем* кадре
        # (last_frame_main_ui_areas, last_frame_popup_areas, last_frame_popup_rect)

        click_processed_in_event_loop = False # Флаг, что клик был обработан здесь

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Обработка ввода текста (если активно окно) ---
            if input_mode and active_input_field:
                if event.type == pygame.KEYDOWN:
                    # ... (весь ваш код для K_BACKSPACE, K_RETURN, K_TAB, event.unicode) ...
                    # Важно: этот ввод обрабатывается сразу
                    pass # Логика остается прежней

            # --- Обработка кликов мыши ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_processed_in_event_loop = True # Отмечаем, что был клик

                # Сначала проверяем клик по попапу, если он активен
                if input_mode and last_frame_popup_rect and last_frame_popup_areas:
                    clicked_popup_element = False
                    for name, rect in last_frame_popup_areas.items():
                        if rect.collidepoint(mouse_pos):
                            clicked_popup_element = True
                            print(f"Popup Click: {name}") # Отладка

                            if name == 'save':
                                # --- Логика сохранения ---
                                task_name = input_data.get('name', '').strip()
                                if task_name: # Проверка, что имя не пустое
                                    # ... (весь ваш код для сборки new_task_data и вызова add_task) ...
                                    new_task_data = {'name': task_name}
                                    task_type_db = None
                                    if input_mode == 'Habit':
                                        task_type_db = 'habits'; habit_type = input_data.get('type', '+-').strip(); new_task_data['type'] = habit_type if habit_type in ['+', '-', '+-'] else '+-' ; # Добавил значения по умолчанию в add_task
                                    elif input_mode == 'Daily':
                                        task_type_db = 'dailies'
                                    elif input_mode == 'To-Do':
                                        task_type_db = 'todos'; new_task_data['notes'] = input_data.get('notes', '').strip()

                                    if task_type_db:
                                        new_id = add_task(task_type_db, new_task_data)
                                        if new_id:
                                            print(f"Added new {input_mode} (ID: {new_id}): {task_name}")
                                            # Обновляем локальные списки
                                            if input_mode == 'Habit': habits = get_tasks('habits')
                                            elif input_mode == 'Daily': dailies = get_tasks('dailies')
                                            elif input_mode == 'To-Do': todos = get_tasks('todos')
                                        else: print(f"Error adding {input_mode}.")
                                    # Сброс после сохранения
                                    input_mode = None; input_data = {}; active_input_field = None
                                else:
                                    print("Error: Task name cannot be empty.")
                                    # Не закрываем окно, даем исправить

                            elif name == 'cancel':
                                print("Popup Cancel Clicked")
                                # Сброс при отмене
                                input_mode = None; input_data = {}; active_input_field = None

                            elif name in ['name', 'type', 'notes']: # Кликнули на поле ввода
                                print(f"Activating input field: {name}")
                                active_input_field = name
                            break # Выходим из цикла проверки кликов попапа
                    # Если кликнули внутри прямоугольника попапа, но не на элемент - можно ничего не делать
                    # или деактивировать поле ввода:
                    # if not clicked_popup_element and last_frame_popup_rect.collidepoint(mouse_pos):
                    #     active_input_field = None
                    # Если кликнули ВНЕ попапа - закрываем его
                    if not last_frame_popup_rect.collidepoint(mouse_pos):
                         print("Clicked outside popup, closing.")
                         input_mode = None; input_data = {}; active_input_field = None

                # Если попап не активен ИЛИ клик был вне его, проверяем основной UI
                elif not input_mode or not (last_frame_popup_rect and last_frame_popup_rect.collidepoint(mouse_pos)):
                    # Используем области основного UI с *прошлого* кадра
                    for area_rect, area_type, item_id, action in last_frame_main_ui_areas:
                         if area_rect.collidepoint(mouse_pos):
                             print(f"Main UI Click: Type={area_type}, ID={item_id}, Action={action}") # Отладка

                             # --- Логика обработки кликов основного UI ---
                             if action == 'add_new':
                                 print(f"Opening input for: {area_type}")
                                 input_mode = area_type.capitalize() # 'Habit', 'Daily', 'To-Do'
                                 input_data = {} # Очищаем данные для нового ввода
                                 active_input_field = 'name' # Активируем первое поле
                                 # Очищаем данные попапа на всякий случай
                                 last_frame_popup_areas = {}
                                 last_frame_popup_rect = None

                             # ... (весь ваш код обработки 'positive', 'negative', 'complete', 'buy', 'equip') ...
                             # Не забудьте обновлять списки (habits, dailies, todos, rewards) и character_data
                             # и вызывать update_character_data(character_data) после изменений

                             elif area_type == 'habits':
                                 # ... (логика для habits) ...
                                 habits = get_tasks('habits'); update_character_data(character_data)
                             elif area_type == 'dailies':
                                 # ... (логика для dailies) ...
                                 dailies = get_tasks('dailies'); update_character_data(character_data)
                             elif area_type == 'todos':
                                  # ... (логика для todos) ...
                                  todos = get_tasks('todos'); update_character_data(character_data)
                             elif area_type == 'reward':
                                  # ... (логика для reward) ...
                                  rewards = get_rewards(); update_character_data(character_data)


                             break # Выходим из цикла проверки кликов основного UI, т.к. клик обработан


        # --- Логика обновления (если нужно, например, анимации) ---
        # ... пока пусто ...

        # --- Отрисовка ---
        screen.blit(BG_SURFACE, (0, 0))
        draw_character_panel(screen, character_data)

        # --- Отрисовка списков и сбор их областей ---
        col_width = (SCREEN_WIDTH - 40) // 3
        col_height = SCREEN_HEIGHT - 160 - 100
        list_y = 140
        # Вызываем функции отрисовки, они возвращают списки [(rect, type, id, action), ...]
        current_habits_clicks = draw_task_list(screen, "Habits", habits, 'habits', 10, list_y, col_width, col_height)
        current_dailies_clicks = draw_task_list(screen, "Dailies", dailies, 'dailies', 15 + col_width, list_y, col_width, col_height)
        current_todos_clicks = draw_task_list(screen, "To-Dos", todos, 'todos', 20 + col_width*2, list_y, col_width, col_height)

        # --- Отрисовка наград и сбор их областей ---
        rewards_y = list_y + col_height + 10
        rewards_height = SCREEN_HEIGHT - rewards_y - 10
        current_rewards_clicks = draw_rewards_panel(screen, rewards, character_data['gold'], 10, rewards_y, SCREEN_WIDTH - 20, rewards_height)

        # Сохраняем все области основного UI для использования на следующем кадре
        current_main_ui_areas = current_habits_clicks + current_dailies_clicks + current_todos_clicks + current_rewards_clicks

        # --- Отрисовка попапа (если активен) и сбор его областей ---
        current_popup_areas = {}
        current_popup_rect = None
        if input_mode:
            # Функция отрисовки возвращает словарь областей и прямоугольник окна
            current_popup_areas, current_popup_rect = draw_input_popup(screen, input_mode, input_data, active_input_field)

        # --- ОБНОВЛЯЕМ ПЕРЕМЕННЫЕ ДЛЯ СЛЕДУЮЩЕГО КАДРА ---
        last_frame_main_ui_areas = current_main_ui_areas
        last_frame_popup_areas = current_popup_areas
        last_frame_popup_rect = current_popup_rect

        # ===================================
        # === 4. ОБНОВЛЕНИЕ ЭКРАНА        ===
        # ===================================
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    # Создаем папку assets, если ее нет
    if not os.path.exists(ASSETS_FOLDER):
        os.makedirs(ASSETS_FOLDER)
        print(f"Created '{ASSETS_FOLDER}' directory. Please place your sprites there.")
        # TODO: Можно добавить скачивание/копирование спрайтов по умолчанию, если их нет

    game_loop()