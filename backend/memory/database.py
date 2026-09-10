"""Compatibility wrapper — persistent memory is implemented in backend.state."""

from backend.state import StateManager, get_connection, init_db

__all__ = ["StateManager", "get_connection", "init_db"]
