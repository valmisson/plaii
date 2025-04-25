"""
Application settings and configuration
"""
import os
from pathlib import Path

# Application metadata
APP_NAME = "Plaii"
APP_VERSION = "0.1.0"

# Paths
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "app" / "assets"

# Database settings
DB_PATH = str(ROOT_DIR / "storage/data/datastore.db")

# UI settings
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768
DEFAULT_PLAYER_HEIGHT = 120
DEFAULT_VIEW_HEIGHT = DEFAULT_WINDOW_HEIGHT - (DEFAULT_PLAYER_HEIGHT * 2.2)
DEFAULT_DURATION_TEXT = '00:00'
DEFAULT_VOLUME = 0.5

# Player settings
DEFAULT_PLACEHOLDER_IMAGE = str(ASSETS_DIR / "album_placeholder.png")
DEFAULT_BATCH_SIZE = 100
