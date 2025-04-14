import unittest
import os
import sqlite3
from datetime import datetime, date
import pygame

# Add this constant at the top of the file
TEST_DB = "test_rpg_life.db"

# Add this function to override the database connection for tests
def get_test_db_connection():
    """Get database connection for tests."""
    return sqlite3.connect(TEST_DB)

# Modify the database.py imports and override the connection
from database import (
    init_db, 
    get_tasks, 
    add_task, 
    update_task, 
    delete_task,
    get_character_data
)
import database
database.get_db_connection = get_test_db_connection  # Override the connection function

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        """Set up test database before each test."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        
        # Initialize test database
        self.conn = get_test_db_connection()
        init_db()

    def tearDown(self):
        """Clean up after each test."""
        self.conn.close()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_character_initialization(self):
        """Test character creation and default values."""
        character = get_character_data()
        self.assertIsNotNone(character)
        self.assertEqual(character['level'], 1)
        self.assertEqual(character['xp'], 0)
        self.assertEqual(character['health'], 100)
        self.assertEqual(character['gold'], 0)

    def test_habit_operations(self):
        """Test CRUD operations for habits."""
        # Test adding a habit
        habit_data = {'name': 'Test Habit'}
        habit_id = add_task('habits', habit_data)
        self.assertIsNotNone(habit_id)

        # Test getting habits
        habits = get_tasks('habits')
        self.assertEqual(len(habits), 1)
        self.assertEqual(habits[0]['name'], 'Test Habit')

        # Test updating a habit
        update_task('habits', habit_id, {'name': 'Updated Habit'})
        habits = get_tasks('habits')
        self.assertEqual(habits[0]['name'], 'Updated Habit')

        # Test deleting a habit
        delete_task('habits', habit_id)
        habits = get_tasks('habits')
        self.assertEqual(len(habits), 0)

    def test_daily_operations(self):
        """Test operations for dailies including completion status."""
        # Add a daily
        daily_data = {'name': 'Test Daily'}
        daily_id = add_task('dailies', daily_data)

        # Test initial state
        dailies = get_tasks('dailies')
        self.assertEqual(len(dailies), 1)
        self.assertEqual(dailies[0]['completed_today'], 0)  # SQLite stores booleans as 0/1
        self.assertEqual(dailies[0]['streak'], 0)

        # Test completing a daily
        today = date.today().isoformat()
        update_task('dailies', daily_id, {
            'completed_today': 1,  # SQLite stores booleans as 0/1
            'streak': 1,
            'last_completed': today
        })
        
        dailies = get_tasks('dailies')
        self.assertEqual(dailies[0]['completed_today'], 1)  # SQLite stores booleans as 0/1
        self.assertEqual(dailies[0]['streak'], 1)

    def test_todo_operations(self):
        """Test operations for todos including completion status."""
        # Add a todo with all required fields
        todo_data = {
            'name': 'Test Todo',
            'notes': 'Test Notes'
        }
        
        # Get initial count
        initial_todos = get_tasks('todos', include_completed=True)
        initial_count = len(initial_todos)

        # Add new todo
        todo_id = add_task('todos', todo_data)
        self.assertIsNotNone(todo_id)

        # Verify todo was added
        todos = get_tasks('todos', include_completed=True)
        self.assertEqual(len(todos), initial_count + 1)
        
        # Find our test todo
        test_todo = next((t for t in todos if t['id'] == todo_id), None)
        self.assertIsNotNone(test_todo)
        self.assertEqual(test_todo['name'], 'Test Todo')
        self.assertEqual(test_todo['notes'], 'Test Notes')
        self.assertEqual(test_todo['completed'], 0)  # SQLite stores booleans as 0/1

        # Test completing a todo
        update_task('todos', todo_id, {'completed': 1})  # SQLite stores booleans as 0/1
        
        # Verify completion - need to include completed todos in query
        todos = get_tasks('todos', include_completed=True)
        updated_todo = next((t for t in todos if t['id'] == todo_id), None)
        self.assertIsNotNone(updated_todo)
        self.assertEqual(updated_todo['completed'], 1)  # SQLite stores booleans as 0/1

        # Verify todo is not in incomplete list
        incomplete_todos = get_tasks('todos', include_completed=False)
        incomplete_todo = next((t for t in incomplete_todos if t['id'] == todo_id), None)
        self.assertIsNone(incomplete_todo)  # Should not be in incomplete list

class TestUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize Pygame for UI tests."""
        pygame.init()
        cls.screen = pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        """Clean up Pygame."""
        pygame.quit()

    def test_button_click_areas(self):
        """Test if click areas are correctly generated."""
        from main import draw_task_list
        
        # Create test tasks with all required fields for each type
        test_habit = {
            'id': 1,
            'name': 'Test Habit',
            'value_xp': 5,
            'value_gold': 1,
            'counter': 0
        }

        test_daily = {
            'id': 1,
            'name': 'Test Daily',
            'completed_today': False,
            'streak': 0,
            'frequency': 'daily',
            'value_xp': 10,
            'value_gold': 5,
            'penalty_hp': 10
        }

        test_todo = {
            'id': 1,
            'name': 'Test Todo',
            'notes': '',
            'completed': False,
            'value_xp': 20,
            'value_gold': 10,
            'difficulty': 1
        }

        # Test habits column
        click_areas = draw_task_list(self.screen, "Habits", [test_habit], 'habits', 10, 140, 250, 400)
        self.assertTrue(any(area[3] == 'edit' for area in click_areas))
        self.assertTrue(any(area[3] == 'delete' for area in click_areas))

        # Test dailies column
        click_areas = draw_task_list(self.screen, "Dailies", [test_daily], 'dailies', 270, 140, 250, 400)
        self.assertTrue(any(area[3] == 'toggle_complete' for area in click_areas))
        self.assertTrue(any(area[3] == 'delete' for area in click_areas))

        # Test todos column
        click_areas = draw_task_list(self.screen, "To-Dos", [test_todo], 'todos', 530, 140, 250, 400)
        self.assertTrue(any(area[3] == 'toggle_complete' for area in click_areas))
        self.assertTrue(any(area[3] == 'delete' for area in click_areas))

def run_tests():
    """Run all tests."""
    unittest.main()

if __name__ == '__main__':
    run_tests() 