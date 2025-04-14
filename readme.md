

# Hierophant: RPG Life Tracker

Turn your daily life into a game! This Pygame application helps you track habits, daily tasks, and to-dos, rewarding you with XP, gold, and virtual items like an RPG character.

**(Optional: Add a screenshot or GIF of the application here)** ![screenshot_placeholder](link_to_your_screenshot.png)

## Features

- **Character Progression:** Level up your character by completing tasks. Track XP, Health, and Gold.
- **Task Types:**
  - **Habits:** Track recurring actions (positive '+', negative '-', or both '+-'). Gain rewards or lose health.
  - **Dailies:** Schedule tasks that repeat daily (or planned weekly/monthly). Lose health if missed. Track completion streaks.
  - **To-Dos:** Manage one-off tasks. They become more valuable (more XP/Gold) the longer they remain undone.
- **Rewards System:**
  - Earn Gold for completing tasks.
  - Spend Gold in the Rewards shop to buy virtual items (Equipment, Pets, Custom).
  - Basic inventory system to see owned items.
- **Consequences:** Lose health for engaging in negative habits or failing to complete Dailies.
- **Simple UI:** Basic interface to view stats, tasks, and rewards.
- **Task Creation:** Add new Habits, Dailies, and To-Dos directly through the UI pop-up.
- **Data Persistence:** Uses SQLite to save your progress between sessions.
- **Daily Reset:** Automatically checks for missed Dailies at the start of a new day.

## Technology

- **Python 3.x**
- **Pygame:** For the graphical interface and event handling.
- **SQLite 3:** For the local database.

## Setup and Installation

1. **Clone or Download:** Get a copy of the project files.
   
   ```bash
   git clone <your-repository-url> # Or download the ZIP
   cd rpg-life-tracker
   ```

2. **Python:** Ensure you have Python 3 installed on your system.

3. **Install Pygame:** Open your terminal or command prompt and install the Pygame library:
   
   ```bash
   pip install pygame
   ```
   
   *(Or `python -m pip install pygame` or `pip3 install pygame` depending on your system setup)*

4. **Assets Folder:** Create an `assets` folder in the main project directory (where `main.py` is located) if it doesn't exist.

5. **Place Sprites:** Copy the required image files into the `assets` folder. The application expects the following filenames (you can replace them with your own, but update the `SPRITES` dictionary in `main.py`):
   
   - `checkmark.png` (For completing tasks)
   - `x_button.png` (Currently unused, but loaded)
   - `character.png` (Your character's avatar)
   - `background.png` (Optional: A tileable background image)
   - `axe.png` (Reward item)
   - `dragon.png` (Reward item)
   - `feather.png` (Reward item)
   - `creature.png` (Reward item)
   - `map_study.png` (Reward item / decoration)

## Running the Application

Navigate to the project directory in your terminal and run the main script:

```bash
python main.py
```



* The application window should appear.
* On the very first run, it will automatically create the `rpg_life.db` database file and the `.last_run_date` file to track daily resets.

## How to Use

* **Character Panel (Top-Left):** Shows your current Level, XP progress, Health bar, and Gold count.
* **Task Lists (Habits, Dailies, To-Dos):**
  * **Habits:** Click the `+` button to record a positive occurrence (gain XP/Gold). Click the `-` button for a negative one (lose Health).
  * **Dailies:** Click the green checkmark button to mark the task as completed for the day (gain XP/Gold, increase streak). Completed dailies are greyed out.
  * **To-Dos:** Click the green checkmark button to mark the task as completed (gain XP/Gold, potentially with a bonus for older tasks). Completed To-Dos disappear from the list.
* **Adding Tasks:** Click the green `+` button next to the title ("Habits", "Dailies", "To-Dos") to open the task creation pop-up window.
  * Click inside the input fields to activate them.
  * Type the required information (Name, Type for Habits, Notes for To-Dos).
  * Click the "Save" button to add the task.
  * Click "Cancel" or click outside the pop-up to close it without saving.
* **Rewards Panel (Bottom):**
  * Browse available items.
  * If you can afford an item (cost shown in Gold), click the gold cost button to purchase it.
  * Owned items are shown with a light green background.
  * For owned 'equipment' or 'pet' items, an "Equip" button may appear. Click it to equip (visual effect currently limited).

## File Structure

```
rpg-life-tracker/
├── main.py             # Main application, Pygame loop, UI rendering
├── database.py         # SQLite database setup and interaction functions
├── assets/             # Folder for image sprites (needs to be created)
│   ├── checkmark.png
│   ├── character.png
│   └── ... (other required sprites)
├── rpg_life.db         # SQLite database file (auto-created)
├── .last_run_date      # Tracks daily reset (auto-created)
└── README.md           # This file
```

## Future Plans / To-Do

* Implement Task Editing and Deletion UI.
* Add visual feedback/effects for leveling up, gaining rewards, losing health.
* Implement actual effects for equipped items (e.g., +% Gold, +Max Health).
* Expand Daily scheduling options (weekly days, specific dates).
* Allow creation of custom user-defined rewards with specific gold costs.
* Add sound effects.
* Improve visual design and UI layout.
* Implement To-Do difficulty settings affecting rewards.
* Add sorting/filtering options for task lists.

## Contributing

Contributions are welcome! Feel free to fork the repository, make improvements, and submit a pull request. Please adhere to standard Python coding practices.

*(Optional: Add specific contribution guidelines if desired)*

## License

*(Optional: Specify a license, e.g., MIT License)*

```

**How to use this:**

1. Save the content above into a file named `README.md` in the root directory of your project (the same place as `main.py`).
2. **Replace Placeholder:** If you have a screenshot, upload it somewhere (like GitHub itself if you're hosting it there) and replace `link_to_your_screenshot.png` with the actual URL. If not, you can remove the `![screenshot_placeholder](...)` line for now.
3. **Update Repository URL:** If you plan to host this on GitHub/GitLab etc., replace `<your-repository-url>` in the `git clone` command with the actual URL.
4. **Add License:** If you choose a license (like MIT), add a `LICENSE` file to your project and mention it in the README.