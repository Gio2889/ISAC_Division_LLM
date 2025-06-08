import sqlite3
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import secrets

class AgentDB:
    def __init__(self):
        self.db_path = "data/databases/agents.db"
        self._init_db()
        self.backend = default_backend()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Check if the table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='agents'
            """)
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS agents (
                        discord_id INTEGER PRIMARY KEY,
                        agent_name TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        clearance_level INTEGER DEFAULT 1
                    )
                """)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def register_agent(self, discord_id: int, agent_name: str, password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = self._derive_key(password, salt)
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO agents (discord_id, agent_name, salt, password_hash) VALUES (?, ?, ?, ?)",
                    (discord_id, agent_name, base64.urlsafe_b64encode(salt).decode(), password_hash.decode())
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def authenticate_agent(self, discord_id: int, password: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT salt, password_hash FROM agents WHERE discord_id = ?",
                (discord_id,)
            )
            result = cursor.fetchone()
            
        if not result:
            return False
            
        salt = base64.urlsafe_b64decode(result[0].encode())
        stored_hash = result[1].encode()
        attempt_hash = self._derive_key(password, salt)
        
        return secrets.compare_digest(attempt_hash, stored_hash)
    
    def get_agent_clearance(self, discord_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT clearance_level FROM agents WHERE discord_id = ?",
                (discord_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0