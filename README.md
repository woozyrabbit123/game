# Project Narco-Syndicate

A deep, turn-based drug trading and crime management simulation game for the terminal, featuring a fully interactive curses-based UI.

## Features
- Advanced curses UI: colored windows, scrolling, and organized layout (header, content, log, input)
- Dynamic regional drug markets with supply/demand, heat, and events
- Player inventory, skills, upgrades, and crypto wallet
- AI rivals, informant system, corrupt officials, and risk events
- Multi-stage Debt Collector storyline (three payments, game over on failure)
- Money laundering, crypto trading, and special events (e.g., "The Setup")

## How to Run
1. **Requirements:**
   - Python 3.10+
   - Windows: Install `windows-curses` via PowerShell:
     ```powershell
     pip install windows-curses
     ```
2. **Start the game:**
   ```powershell
   python main.py
   ```
   The game will launch in full-screen terminal mode using curses.

## Controls & UI
- **Navigation:**
  - Use the main menu to select actions (type the number/letter and press Enter)
  - In market/inventory views: scroll with Up/Down arrows or `j`/`k`, press `q` or Enter to exit
- **Input:**
  - All prompts appear at the bottom input line
  - Enter values as instructed (e.g., `Coke PURE 10`)
- **Colors:**
  - Header: yellow on blue
  - Success: green
  - Warnings/Errors: red
  - Menu highlights: cyan
  - Input: magenta
- **Log window:**
  - Shows recent messages, events, and errors

## Game Structure
- **Regions:** Downtown, The Docks, Suburbia (each with unique markets)
- **Events:** Market events, police stops, rival actions, and special opportunities
- **Debt Collector:** Three payments due on specific days; failure results in game over
- **Skills/Upgrades:** Unlock market intuition, digital footprint, increase capacity, buy secure phone
- **Crypto:** Buy/sell/trade DC, VC, SC; launder money via Tech Contact

## Technologies Used
- Python 3.10+
- Pygame (for the graphical UI version)
- Textual (for the terminal UI version)
- curses (for the terminal UI, especially `windows-curses` on Windows)

## Project Structure
- `src/`: Contains the main source code for the game.
- `src/core/`: Core game logic, data structures (e.g., drugs, regions, player inventory), and enums.
- `src/mechanics/`: Game mechanics such as event management and market impact calculations.
- `src/ui_pygame/`: Implementation of the Pygame-based graphical user interface.
- `src/ui_textual/`: Implementation of the Textual-based terminal user interface.

## Testing
The project includes a suite of tests located in the `tests/` directory.
Currently, these tests primarily cover the core game logic (`tests/core/`) and game mechanics (`tests/mechanics/`).
To run the tests, navigate to the root directory of the project in your terminal and run the following command:
```bash
python -m unittest discover tests
```

## Known Limitations
- Terminal resizing during play may cause display issues
- Only tested on Windows with `windows-curses`
- For best experience, use a terminal window at least 80x24

## Credits
- Game design and code: You & GitHub Copilot
- Curses UI refactor: May 2025

Enjoy running your own syndicate!
