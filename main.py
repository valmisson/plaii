"""
Plaii Music Player - Main Application Entry Point
"""
from flet import app

from app.ui.app import AppWindow

if __name__ == '__main__':
    app(target=AppWindow)
