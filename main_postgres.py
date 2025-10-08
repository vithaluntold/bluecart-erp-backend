# Temporary compatibility file for Render deployment
# This file imports the actual app from main.py
# TODO: Update Render start command to use "main:app" instead of "main_postgres:app"

from main import app

# Re-export the app so uvicorn can find it
__all__ = ['app']