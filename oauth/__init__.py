"""
OAuth 2.1 module for MCP Video Transcriber

This module provides complete OAuth 2.1 authentication and authorization
for the MCP server, including:
- Dynamic Client Registration (RFC 7591)
- Authorization Code Grant with PKCE
- Client Credentials Grant  
- JWT Access Tokens
- Metadata Discovery (RFC 8414, RFC 9728)
"""

from .auth import create_access_token, verify_access_token, get_current_user
from .endpoints import create_oauth_router
from .models import OAuthClient, AuthCode, RefreshToken

__all__ = [
    "create_access_token",
    "verify_access_token",
    "get_current_user",
    "create_oauth_router",
    "OAuthClient",
    "AuthCode",
    "RefreshToken"
]
