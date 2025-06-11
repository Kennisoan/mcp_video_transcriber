"""
Database management for OAuth 2.1 persistence

This module handles SQLite database operations for OAuth clients,
authorization codes, and refresh tokens using SQLAlchemy ORM.
"""

import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Optional, Dict, Any

from oauth.models import Base, OAuthClient, AuthCode, RefreshToken
from config import Config


class DatabaseManager:
    """Manages OAuth database operations with SQLAlchemy"""

    def __init__(self):
        # Determine database path
        if Config.DATABASE_PATH:
            db_path = Config.DATABASE_PATH
        else:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "oauth.db")

        # Create database engine
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # OAuth Client operations
    def create_client(self, client_data: Dict[str, Any]) -> None:
        """Create a new OAuth client"""
        with self.get_session() as session:
            client = OAuthClient(
                client_id=client_data["client_id"],
                client_secret=client_data["client_secret"],
                client_name=client_data["client_name"],
                redirect_uris=json.dumps(client_data["redirect_uris"]),
                grant_types=json.dumps(client_data["grant_types"]),
                scope=client_data["scope"],
                created_at=client_data["created_at"]
            )
            session.add(client)

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth client by ID"""
        with self.get_session() as session:
            client = session.query(OAuthClient).filter(
                OAuthClient.client_id == client_id).first()
            if client:
                return {
                    "client_id": client.client_id,
                    "client_secret": client.client_secret,
                    "client_name": client.client_name,
                    "redirect_uris": json.loads(client.redirect_uris),
                    "grant_types": json.loads(client.grant_types),
                    "scope": client.scope,
                    "created_at": client.created_at
                }
            return None

    def delete_client(self, client_id: str) -> bool:
        """Delete OAuth client"""
        with self.get_session() as session:
            client = session.query(OAuthClient).filter(
                OAuthClient.client_id == client_id).first()
            if client:
                session.delete(client)
                return True
            return False

    # Authorization Code operations
    def create_auth_code(self, code_data: Dict[str, Any]) -> None:
        """Create authorization code"""
        with self.get_session() as session:
            auth_code = AuthCode(
                code=code_data["code"],
                client_id=code_data["client_id"],
                redirect_uri=code_data["redirect_uri"],
                scope=code_data["scope"],
                code_challenge=code_data.get("code_challenge"),
                code_challenge_method=code_data.get("code_challenge_method"),
                created_at=code_data["created_at"],
                expires_at=code_data["expires_at"]
            )
            session.add(auth_code)

    def get_auth_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get authorization code"""
        with self.get_session() as session:
            auth_code = session.query(AuthCode).filter(
                AuthCode.code == code).first()
            if auth_code:
                return {
                    "code": auth_code.code,
                    "client_id": auth_code.client_id,
                    "redirect_uri": auth_code.redirect_uri,
                    "scope": auth_code.scope,
                    "code_challenge": auth_code.code_challenge,
                    "code_challenge_method": auth_code.code_challenge_method,
                    "created_at": auth_code.created_at,
                    "expires_at": auth_code.expires_at
                }
            return None

    def delete_auth_code(self, code: str) -> bool:
        """Delete authorization code"""
        with self.get_session() as session:
            auth_code = session.query(AuthCode).filter(
                AuthCode.code == code).first()
            if auth_code:
                session.delete(auth_code)
                return True
            return False

    # Refresh Token operations
    def create_refresh_token(self, token_data: Dict[str, Any]) -> None:
        """Create refresh token"""
        with self.get_session() as session:
            refresh_token = RefreshToken(
                token=token_data["token"],
                client_id=token_data["client_id"],
                scope=token_data["scope"],
                created_at=token_data["created_at"]
            )
            session.add(refresh_token)

    def get_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get refresh token"""
        with self.get_session() as session:
            refresh_token = session.query(RefreshToken).filter(
                RefreshToken.token == token).first()
            if refresh_token:
                return {
                    "token": refresh_token.token,
                    "client_id": refresh_token.client_id,
                    "scope": refresh_token.scope,
                    "created_at": refresh_token.created_at
                }
            return None

    def delete_refresh_token(self, token: str) -> bool:
        """Delete refresh token"""
        with self.get_session() as session:
            refresh_token = session.query(RefreshToken).filter(
                RefreshToken.token == token).first()
            if refresh_token:
                session.delete(refresh_token)
                return True
            return False

    # Cleanup operations
    def cleanup_expired_codes(self) -> int:
        """Remove expired authorization codes"""
        import time
        current_time = time.time()

        with self.get_session() as session:
            expired_codes = session.query(AuthCode).filter(
                AuthCode.expires_at < current_time).all()
            count = len(expired_codes)
            for code in expired_codes:
                session.delete(code)
            return count

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.get_session() as session:
            return {
                "clients": session.query(OAuthClient).count(),
                "auth_codes": session.query(AuthCode).count(),
                "refresh_tokens": session.query(RefreshToken).count()
            }


# Global database manager instance
db_manager = DatabaseManager()
