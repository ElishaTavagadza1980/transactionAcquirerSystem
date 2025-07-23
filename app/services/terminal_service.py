from app.data_access.terminal_supabase import (
    dataCreateTerminal,
    dataGetTerminals,
    dataGetTerminal,
    dataUpdateTerminal,
    dataDeleteTerminal,
)
import logging
from typing import List, Optional
from fastapi import HTTPException
import json
from app.models.terminal_model import Terminal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalService:
    def __init__(self):
        self.logger = logger

    def get_terminals(self) -> List[dict]:
        try:
            terminals = dataGetTerminals()
            self.logger.info(f"Service retrieved {len(terminals)} terminals")
            return terminals
        except Exception as e:
            self.logger.error(f"Error retrieving terminals: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve terminals: {str(e)}")

    def search_terminals(self, filter_field: str, search_value: str = None) -> List[dict]:
        try:
            all_terminals = dataGetTerminals()
            self.logger.debug(f"Raw terminals data: {json.dumps(all_terminals, indent=2)}")
            filtered_terminals = all_terminals

            if search_value:
                if filter_field == "terminal_id":
                    filtered_terminals = [t for t in filtered_terminals if t.get("terminal_id") == search_value]
                elif filter_field == "terminal_serial_number":
                    filtered_terminals = [t for t in filtered_terminals if search_value.lower() in t.get("terminal_serial_number", "").lower()]
                elif filter_field == "status":
                    filtered_terminals = [t for t in filtered_terminals if t.get("status", "").lower() == search_value.lower()]
                else:
                    filtered_terminals = []

            
            valid_terminals = []
            for terminal in filtered_terminals:
                try:
                    Terminal(**terminal)
                    valid_terminals.append(terminal)
                except Exception as e:
                    self.logger.error(f"Invalid terminal data: {str(e)}")
                    continue

            self.logger.info(f"{len(valid_terminals)} terminals matched {filter_field}='{search_value}'")
            return valid_terminals
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to search terminals: {str(e)}")

    def get_terminal(self, terminal_id: str) -> Optional[dict]:
        try:
            terminal = dataGetTerminal(terminal_id)
            if terminal:
                self.logger.info(f"Retrieved terminal: {terminal_id}")
                return terminal
            self.logger.info(f"Terminal not found: {terminal_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting terminal {terminal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve terminal: {str(e)}")

    def create_terminal(self, terminal: Terminal) -> dict:
        try:
            result = dataCreateTerminal(terminal)
            if result:
                self.logger.info(f"Created terminal: {terminal.terminal_id}")
                return result
            raise HTTPException(status_code=500, detail="Failed to create terminal")
        except Exception as e:
            self.logger.error(f"Create error {terminal.terminal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create terminal: {str(e)}")

    def update_terminal(self, terminal_id: str, updates: dict) -> dict:
        try:
            result = dataUpdateTerminal(terminal_id, updates)
            if result:
                self.logger.info(f"Updated terminal: {terminal_id}")
                return result
            raise HTTPException(status_code=404, detail="Terminal not found")
        except Exception as e:
            self.logger.error(f"Update error {terminal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update terminal: {str(e)}")

    def delete_terminal(self, terminal_id: str) -> dict:
        try:
            result = dataDeleteTerminal(terminal_id)
            if result:
                self.logger.info(f"Deleted terminal: {terminal_id}")
                return result
            raise HTTPException(status_code=404, detail="Terminal not found")
        except Exception as e:
            self.logger.error(f"Delete error {terminal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete terminal: {str(e)}")