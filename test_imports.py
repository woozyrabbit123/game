import sys, os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Python path: {sys.path}")
print(f"Working directory: {project_root}")
print(f"Directory contents: {os.listdir(project_root)}")

try:
    import src.narco_configs as game_configs

    print("Successfully imported game_configs")
except ImportError as e:
    print(f"Failed to import game_configs: {e}")
    import traceback

    traceback.print_exc()

try:
    import src.game_state

    print("Successfully imported game_state")
except ImportError as e:
    print(f"Failed to import game_state: {e}")
    import traceback

    traceback.print_exc()

try:
    from src.core import enums

    print("Successfully imported enums")
except ImportError as e:
    print(f"Failed to import enums: {e}")
    import traceback

    traceback.print_exc()
