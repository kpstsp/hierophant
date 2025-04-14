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
LIGHT_BLUE = (173, 216, 230)  # Light blue color for active input fields

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
    # !!! ИЗМЕНЕНИЕ: Рассчитываем высоту динамически СНАЧАЛА !!!
    # Определяем поля
    fields_to_draw = []
    if mode == 'Habit': fields_to_draw = [('name', 'Name:'), ('type', 'Type (+/-/+-):')]
    elif mode == 'Daily': fields_to_draw = [('name', 'Name:')]
    elif mode == 'To-Do': fields_to_draw = [('name', 'Name:'), ('notes', 'Notes (opt):')]
    else: return {}, None # На случай неизвестного режима

    if not fields_to_draw and mode not in ['Habit', 'Daily', 'To-Do']: # Добавил проверку, если mode правильный, но список полей пуст
         print(f"  ERROR in draw_input_popup: Unknown mode '{mode}' or empty fields_to_draw.")
         return {}, None

    num_fields = len(fields_to_draw)
    field_height = 30
    field_spacing = 10 # Расстояние между полями
    button_height = 30
    padding_top = 60    # Место для заголовка и отступа сверху
    padding_bottom = 15 # Отступ снизу под кнопками
    button_v_spacing = 20 # Отступ над кнопками

    # Рассчитываем необходимую высоту
    required_height = padding_top + (num_fields * (field_height + field_spacing)) + button_v_spacing + button_height + padding_bottom
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - required_height) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, required_height)


     # !!! ДОБАВИТЬ ПРОВЕРКИ ЗДЕСЬ !!!
    print(f"  Inside draw_input_popup: mode={mode}, num_fields={num_fields}")
    print(f"  Calculated required_height: {required_height}")
    print(f"  Calculated popup_rect: {popup_rect}")
    if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).contains(popup_rect):
        print(f"  WARNING: popup_rect {popup_rect} is outside screen bounds!")
    elif popup_rect.width <= 0 or popup_rect.height <= 0:
        print(f"  WARNING: popup_rect {popup_rect} has zero or negative size!")
    # !!! КОНЕЦ ДОБАВЛЕННЫХ ПРОВЕРОК !!!


    # 1. Рисуем фон и рамку правильного размера
    pygame.draw.rect(surface, INPUT_BOX_COLOR, popup_rect, border_radius=10)
    pygame.draw.rect(surface, INPUT_BOX_BORDER_COLOR, popup_rect, 2, border_radius=10)
    # print(f"Drawing popup background with final rect: {popup_rect}") # Отладка

    # 2. Рисуем заголовок
    title = f"Add New {mode.capitalize()}"
    title_surf = FONT_MEDIUM.render(title, True, BLACK)
    surface.blit(title_surf, (popup_rect.x + 15, popup_rect.y + 15))

    # 3. Рисуем поля ввода
    current_field_y = popup_rect.y + padding_top # Начальная Y координата для полей
    label_width = 80
    input_width = popup_width - label_width - 40
    click_areas = {} # Сбрасываем здесь, т.к. области зависят от финальных координат

    for field_key, label_text in fields_to_draw:
        # Метка
        label_surf = FONT_SMALL.render(label_text, True, BLACK)
        surface.blit(label_surf, (popup_rect.x + 15, current_field_y + 5))

        # Поле ввода
        input_rect = pygame.Rect(popup_rect.x + label_width + 15, current_field_y, input_width, field_height)
        border_color = INPUT_ACTIVE_BORDER_COLOR if active_field == field_key else INPUT_BOX_BORDER_COLOR
        pygame.draw.rect(surface, WHITE, input_rect)
        pygame.draw.rect(surface, border_color, input_rect, 1)
        click_areas[field_key] = input_rect # Добавляем поле в кликабельные зоны

        # Текст внутри поля + Курсор
        text_to_render = input_data.get(field_key, '')
        text_surf = FONT_SMALL.render(text_to_render, True, INPUT_TEXT_COLOR)
        text_rect_in_box = text_surf.get_rect(topleft=(input_rect.x + 5, input_rect.y + 5))
        # Ограничиваем ширину текста для отрисовки
        visible_width = min(text_rect_in_box.width, input_rect.width - 10)
        surface.blit(text_surf, text_rect_in_box, area=pygame.Rect(0, 0, visible_width, text_rect_in_box.height))

        if active_field == field_key:
            cursor_x = input_rect.x + 5 + visible_width # Позиция курсора после видимого текста
            cursor_x = min(cursor_x, input_rect.right - 5) # Не вылезаем за поле
            if pygame.time.get_ticks() % 1000 < 500:
                 pygame.draw.line(surface, BLACK, (cursor_x, input_rect.y + 5), (cursor_x, input_rect.y + field_height - 5), 1)

        # Обновляем Y для следующего поля
        current_field_y += field_height + field_spacing

    # 4. Рисуем кнопки Save и Cancel
    # Y координата для кнопок = последняя Y поля + отступ над кнопками
    button_y = current_field_y + button_v_spacing
    button_width = 100
    # Центрируем кнопки относительно центра попапа по X
    save_rect = pygame.Rect(popup_rect.centerx - button_width - 10, button_y, button_width, button_height)
    cancel_rect = pygame.Rect(popup_rect.centerx + 10, button_y, button_width, button_height)

    pygame.draw.rect(surface, GREEN, save_rect, border_radius=5)
    pygame.draw.rect(surface, RED, cancel_rect, border_radius=5)

    save_text = FONT_SMALL.render("Save", True, WHITE)
    cancel_text = FONT_SMALL.render("Cancel", True, WHITE)
    surface.blit(save_text, save_text.get_rect(center=save_rect.center))
    surface.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

    # Добавляем кнопки в кликабельные зоны
    click_areas['save'] = save_rect
    click_areas['cancel'] = cancel_rect
    # print(f"  Drew Save button at {save_rect}") # Отладка
    # print(f"  Drew Cancel button at {cancel_rect}") # Отладка

    # Возвращаем собранные области и финальный прямоугольник
    return click_areas, popup_rect

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
        pygame.draw.rect(surface, WHITE, task_rect, border_radius=3)
        pygame.draw.rect(surface, DARK_GRAY, task_rect, 1, border_radius=3)

        task_name_rect = pygame.Rect(task_rect.left + 5, task_rect.top + 5, task_rect.width - 70, task_rect.height - 10)
        draw_text(surface, task['name'], FONT_SMALL, BLACK, task_name_rect)

        if task_type == 'habits':
            # Edit button with feather icon
            edit_rect = pygame.Rect(task_rect.right - button_size*2 - 10, task_rect.centery - button_size // 2, button_size, button_size)
            pygame.draw.rect(surface, BLUE, edit_rect, border_radius=3)
            surface.blit(SPRITES['feather'], edit_rect.topleft)
            click_areas.append((edit_rect, task_type, task['id'], 'edit'))

        elif task_type == 'dailies':
            check_rect = pygame.Rect(task_rect.right - button_size*2 - 10, task_rect.centery - button_size // 2, button_size, button_size)
            if task['completed_today']:
                pygame.draw.rect(surface, GREEN, check_rect, border_radius=3)
                surface.blit(SPRITES['checkmark'], check_rect.topleft)
            else:
                pygame.draw.rect(surface, RED, check_rect, border_radius=3)
                surface.blit(SPRITES['x_button'], check_rect.topleft)
                click_areas.append((check_rect, task_type, task['id'], 'toggle_complete'))
            
            streak_text = f"Streak: {task.get('streak', 0)}"
            streak_surf = FONT_SMALL.render(streak_text, True, BLUE)
            surface.blit(streak_surf, (task_rect.left + 5, task_rect.bottom - 15))

        elif task_type == 'todos':
            check_rect = pygame.Rect(task_rect.right - button_size*2 - 10, task_rect.centery - button_size // 2, button_size, button_size)
            if task['completed']:
                pygame.draw.rect(surface, GREEN, check_rect, border_radius=3)
                surface.blit(SPRITES['checkmark'], check_rect.topleft)
            else:
                pygame.draw.rect(surface, RED, check_rect, border_radius=3)
                surface.blit(SPRITES['x_button'], check_rect.topleft)
                click_areas.append((check_rect, task_type, task['id'], 'toggle_complete'))

        # Add delete button for all task types
        delete_rect = pygame.Rect(task_rect.right - button_size - 5, task_rect.centery - button_size // 2, button_size, button_size)
        pygame.draw.rect(surface, DARK_GRAY, delete_rect, border_radius=3)
        delete_text = FONT_MEDIUM.render("×", True, WHITE)
        surface.blit(delete_text, delete_text.get_rect(center=delete_rect.center))
        click_areas.append((delete_rect, task_type, task['id'], 'delete'))

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

def draw_edit_popup(surface, task_data, active_field):
    """Рисует всплывающее окно для редактирования задачи."""
    popup_width = 400
    popup_height = 200
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    # Draw popup background
    pygame.draw.rect(surface, WHITE, popup_rect, border_radius=5)
    pygame.draw.rect(surface, BLACK, popup_rect, 1, border_radius=5)

    # Title
    title_surf = FONT_MEDIUM.render("Edit Habit", True, BLACK)
    title_rect = title_surf.get_rect(centerx=popup_rect.centerx, top=popup_rect.top + 20)
    surface.blit(title_surf, title_rect)

    # Input fields
    field_height = 30
    field_width = popup_width - 60
    fields = {}

    # Name field
    name_label = FONT_SMALL.render("Name:", True, BLACK)
    name_rect = pygame.Rect(popup_x + 30, popup_y + 60, field_width, field_height)
    pygame.draw.rect(surface, WHITE if active_field != 'name' else LIGHT_BLUE, name_rect, border_radius=3)
    pygame.draw.rect(surface, BLACK, name_rect, 1, border_radius=3)
    name_text = FONT_SMALL.render(task_data.get('name', ''), True, BLACK)
    surface.blit(name_label, (name_rect.left, name_rect.top - 20))
    surface.blit(name_text, (name_rect.left + 5, name_rect.centery - name_text.get_height()//2))
    fields['name'] = name_rect

    # Type field
    type_label = FONT_SMALL.render("Type (+/-/+-):", True, BLACK)
    type_rect = pygame.Rect(popup_x + 30, popup_y + 120, field_width, field_height)
    pygame.draw.rect(surface, WHITE if active_field != 'type' else LIGHT_BLUE, type_rect, border_radius=3)
    pygame.draw.rect(surface, BLACK, type_rect, 1, border_radius=3)
    type_text = FONT_SMALL.render(task_data.get('type', ''), True, BLACK)
    surface.blit(type_label, (type_rect.left, type_rect.top - 20))
    surface.blit(type_text, (type_rect.left + 5, type_rect.centery - type_text.get_height()//2))
    fields['type'] = type_rect

    # Buttons
    button_width = 80
    button_height = 30
    button_y = popup_rect.bottom - 50

    save_rect = pygame.Rect(popup_rect.centerx - button_width - 10, button_y, button_width, button_height)
    pygame.draw.rect(surface, GREEN, save_rect, border_radius=3)
    save_text = FONT_SMALL.render("Save", True, WHITE)
    surface.blit(save_text, save_text.get_rect(center=save_rect.center))
    fields['save'] = save_rect

    cancel_rect = pygame.Rect(popup_rect.centerx + 10, button_y, button_width, button_height)
    pygame.draw.rect(surface, RED, cancel_rect, border_radius=3)
    cancel_text = FONT_SMALL.render("Cancel", True, WHITE)
    surface.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))
    fields['cancel'] = cancel_rect

    return fields, popup_rect

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

    edit_mode = None
    edit_data = {}
    active_edit_field = None

    last_frame_main_ui_areas = []
    last_frame_popup_areas = {}
    last_frame_popup_rect = None

    skip_first_popup_click = False  # Новый флаг

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and input_mode and active_input_field:
                current_text = input_data.get(active_input_field, '')

                if event.key == pygame.K_BACKSPACE:
                    input_data[active_input_field] = current_text[:-1]
                elif event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_TAB:
                    fields = [f for f in last_frame_popup_areas if f not in ['save', 'cancel']]
                    if fields:
                        try:
                            current_index = fields.index(active_input_field)
                            next_index = (current_index + 1) % len(fields)
                            active_input_field = fields[next_index]
                        except:
                            active_input_field = fields[0]
                elif event.unicode.isprintable():
                    input_data[active_input_field] = current_text + event.unicode
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if skip_first_popup_click:
                    skip_first_popup_click = False
                    continue

                if input_mode and last_frame_popup_rect and last_frame_popup_areas:
                    clicked_popup_element = False
                    for name, rect in last_frame_popup_areas.items():
                        if name not in ['save', 'cancel'] and rect.collidepoint(mouse_pos):
                            active_input_field = name
                            clicked_popup_element = True
                            break

                    if not clicked_popup_element:
                        for name, rect in last_frame_popup_areas.items():
                            if name in ['save', 'cancel'] and rect.collidepoint(mouse_pos):
                                if name == 'save':
                                    task_name = input_data.get('name', '').strip()
                                    if task_name:
                                        new_task_data = {'name': task_name}
                                        task_type_db = None
                                        if input_mode == 'Habit':
                                            task_type_db = 'habits'
                                            habit_type = input_data.get('type', '+-').strip()
                                            new_task_data['type'] = habit_type if habit_type in ['+', '-', '+-'] else '+-'
                                        elif input_mode == 'Daily':
                                            task_type_db = 'dailies'
                                        elif input_mode == 'To-Do':
                                            task_type_db = 'todos'
                                            new_task_data['notes'] = input_data.get('notes', '').strip()

                                        if task_type_db:
                                            new_id = add_task(task_type_db, new_task_data)
                                            if new_id:
                                                if input_mode == 'Habit': habits = get_tasks('habits')
                                                elif input_mode == 'Daily': dailies = get_tasks('dailies')
                                                elif input_mode == 'To-Do': todos = get_tasks('todos')
                                        input_mode = None
                                        input_data = {}
                                        active_input_field = None
                                        last_frame_popup_rect = None
                                        last_frame_popup_areas = {}
                                    else:
                                        print("Task name cannot be empty.")
                                elif name == 'cancel':
                                    input_mode = None
                                    input_data = {}
                                    active_input_field = None
                                    last_frame_popup_rect = None
                                    last_frame_popup_areas = {}
                                break

                    if last_frame_popup_rect and last_frame_popup_rect.collidepoint(mouse_pos) and not clicked_popup_element:
                        active_input_field = None
                    elif last_frame_popup_rect and not last_frame_popup_rect.collidepoint(mouse_pos):
                        input_mode = None
                        input_data = {}
                        active_input_field = None
                        last_frame_popup_rect = None
                        last_frame_popup_areas = {}

                elif edit_mode:
                    # Handle edit popup clicks
                    clicked_popup_element = False
                    for field_name, field_rect in last_frame_popup_areas.items():
                        if field_rect.collidepoint(mouse_pos):
                            clicked_popup_element = True
                            if field_name in ['name', 'type']:
                                active_edit_field = field_name
                            elif field_name == 'save':
                                # Update the task in database
                                if edit_data.get('name'):  # Ensure name is not empty
                                    update_task('habits', edit_data['id'], {
                                        'name': edit_data['name'],
                                        'type': edit_data.get('type', '+-')
                                    })
                                    habits = get_tasks('habits')  # Refresh habits list
                                    edit_mode = None
                                    edit_data = {}
                                    active_edit_field = None
                            elif field_name == 'cancel':
                                edit_mode = None
                                edit_data = {}
                                active_edit_field = None
                            break

                elif not input_mode:
                    for area_rect, area_type, item_id, action in last_frame_main_ui_areas:
                        if area_rect.collidepoint(mouse_pos):
                            if action == 'add_new':
                                type_map = {'habits': 'Habit', 'dailies': 'Daily', 'todos': 'To-Do'}
                                input_mode = type_map.get(area_type, None)
                                input_data = {}
                                active_input_field = 'name'
                                last_frame_popup_areas = {}
                                last_frame_popup_rect = None
                                skip_first_popup_click = True
                            elif action == 'delete':
                                # Handle deletion for all task types
                                delete_task(area_type, item_id)
                                # Refresh the appropriate task list
                                if area_type == 'habits':
                                    habits = get_tasks('habits')
                                elif area_type == 'dailies':
                                    dailies = get_tasks('dailies')
                                elif area_type == 'todos':
                                    todos = get_tasks('todos')
                            elif action == 'toggle_complete':
                                if area_type == 'dailies':
                                    # Get current task data
                                    task = next((t for t in dailies if t['id'] == item_id), None)
                                    if task:
                                        # Toggle completion status
                                        new_status = not task['completed_today']
                                        # Update streak if completing
                                        if new_status:
                                            streak = task.get('streak', 0) + 1
                                            update_task('dailies', item_id, {
                                                'completed_today': new_status,
                                                'streak': streak,
                                                'last_completed': datetime.date.today().isoformat()
                                            })
                                        else:
                                            # If unchecking, just update completed_today
                                            update_task('dailies', item_id, {'completed_today': new_status})
                                        # Refresh dailies list
                                        dailies = get_tasks('dailies')
                                
                                elif area_type == 'todos':
                                    # Toggle completion status for todo
                                    task = next((t for t in todos if t['id'] == item_id), None)
                                    if task:
                                        new_status = not task['completed']
                                        update_task('todos', item_id, {'completed': new_status})
                                        # Refresh todos list
                                        todos = get_tasks('todos')
                            elif action == 'edit' and area_type == 'habits':
                                # Get task data and enter edit mode
                                task = next((t for t in habits if t['id'] == item_id), None)
                                if task:
                                    edit_mode = True
                                    edit_data = task.copy()
                                    active_edit_field = 'name'
                            # Остальная логика UI...
                            break


        # --- Логика обновления (если нужно, например, анимации) ---
        # ... пока пусто ...

        # --- Отрисовка ---
        screen.blit(BG_SURFACE, (0, 0))
        draw_character_panel(screen, character_data)

        col_width = (SCREEN_WIDTH - 40) // 3
        col_height = SCREEN_HEIGHT - 160 - 100
        list_y = 140
        current_habits_clicks = draw_task_list(screen, "Habits", habits, 'habits', 10, list_y, col_width, col_height)
        current_dailies_clicks = draw_task_list(screen, "Dailies", dailies, 'dailies', 15 + col_width, list_y, col_width, col_height)
        current_todos_clicks = draw_task_list(screen, "To-Dos", todos, 'todos', 20 + col_width*2, list_y, col_width, col_height)

        rewards_y = list_y + col_height + 10
        rewards_height = SCREEN_HEIGHT - rewards_y - 10
        current_rewards_clicks = draw_rewards_panel(screen, rewards, character_data['gold'], 10, rewards_y, SCREEN_WIDTH - 20, rewards_height)

        current_main_ui_areas = current_habits_clicks + current_dailies_clicks + current_todos_clicks + current_rewards_clicks

        current_popup_areas = {}
        current_popup_rect = None
        print(f"[DRAW PHASE] Checking if popup should draw. input_mode = {input_mode}")
        if input_mode:
            # Функция отрисовки использует ТЕКУЩЕЕ состояние input_data и active_input_field
            current_popup_areas, current_popup_rect = draw_input_popup(screen, input_mode, input_data, active_input_field)
            # Убери или закомментируй старый print внутри if, чтобы не дублировать
            # print(f"  Drew popup. Areas: {list(current_popup_areas.keys())}, Rect: {current_popup_rect}")
            if current_popup_rect: # Дополнительная проверка, что rect вернулся
                 print(f"  Drew popup. Final Rect: {current_popup_rect}")
            else:
                 print("  WARNING: draw_input_popup returned None for rect!")

        if edit_mode:
            current_popup_areas, current_popup_rect = draw_edit_popup(screen, edit_data, active_edit_field)
            last_frame_popup_areas = current_popup_areas
            last_frame_popup_rect = current_popup_rect

        # ОБНОВЛЯЕМ ПЕРЕМЕННЫЕ ДЛЯ СЛЕДУЮЩЕГО КАДРА
        last_frame_main_ui_areas = current_main_ui_areas
        last_frame_popup_areas = current_popup_areas
        last_frame_popup_rect = current_popup_rect
        # print(f"End of frame. Last popup areas: {list(last_frame_popup_areas.keys())}") # Отладка

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