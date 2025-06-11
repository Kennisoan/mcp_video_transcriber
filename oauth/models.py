"""
OAuth 2.1 data models for SQLite persistence
"""

from sqlalchemy import Column, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OAuthClient(Base):
    """OAuth client registration data"""
    __tablename__ = "oauth_clients"

    client_id = Column(String(255), primary_key=True)
    client_secret = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    redirect_uris = Column(Text, nullable=False)  # JSON string
    grant_types = Column(Text, nullable=False)    # JSON string
    scope = Column(Text, nullable=False)
    created_at = Column(Float, nullable=False)


class AuthCode(Base):
    """Authorization codes for OAuth flows"""
    __tablename__ = "auth_codes"

    code = Column(String(255), primary_key=True)
    client_id = Column(String(255), nullable=False)
    redirect_uri = Column(String(255), nullable=False)
    scope = Column(Text, nullable=False)
    code_challenge = Column(String(255), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)


class RefreshToken(Base):
    """Refresh tokens for token renewal"""
    __tablename__ = "refresh_tokens"

    token = Column(String(255), primary_key=True)
    client_id = Column(String(255), nullable=False)
    scope = Column(Text, nullable=False)
    created_at = Column(Float, nullable=False)
