# Project Narco-Syndicate Source Code Structure

This directory contains the main source code for the Narco-Syndicate game.

## Directory Structure

- `core/`: Core game logic and data structures
  - Contains player inventory, region management, market events, etc.
  
- `mechanics/`: Game mechanics and systems
  - Event management
  - Market impact calculations
  
- `ui_pygame/`: Pygame-based graphical user interface
  - Main application (app.py)
  - UI components and themes
  - Various game view implementations
  
- `ui_textual/`: Textual-based terminal user interface
  - Main application (app.py)
  - Custom widgets
  - Terminal UI styles and components

## Configuration

- `game_configs.py`: Global game configuration and constants
- `game_state.py`: Game state management
