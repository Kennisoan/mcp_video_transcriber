"""
OAuth 2.1 API Endpoints (RFC compliant)

Implements:
- RFC 8414: OAuth 2.0 Authorization Server Metadata
- RFC 9728: OAuth 2.0 Protected Resource Metadata  
- RFC 7591: OAuth 2.0 Dynamic Client Registration
- OAuth 2.1: Authorization and Token endpoints
"""

import time
import json
import secrets
import hashlib
import base64
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse

from config import Config
from database import db_manager
from .auth import create_access_token, get_current_user


def create_oauth_router() -> APIRouter:
    """Create and configure the OAuth API router"""
    router = APIRouter()

    # OAuth 2.0 Authorization Server Metadata (RFC 8414)
    @router.get("/.well-known/oauth-authorization-server")
    async def authorization_server_metadata():
        """OAuth 2.0 Authorization Server Metadata endpoint"""
        return {
            "issuer": Config.SERVER_URL,
            "authorization_endpoint": f"{Config.SERVER_URL}/authorize",
            "token_endpoint": f"{Config.SERVER_URL}/token",
            "registration_endpoint": f"{Config.SERVER_URL}/register",
            "scopes_supported": Config.SUPPORTED_SCOPES,
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            "revocation_endpoint": f"{Config.SERVER_URL}/revoke"
        }

    # OAuth 2.0 Protected Resource Metadata (RFC 9728)
    @router.get("/.well-known/oauth-protected-resource")
    async def protected_resource_metadata():
        """OAuth 2.0 Protected Resource Metadata endpoint"""
        return {
            "resource": Config.SERVER_URL,
            "authorization_servers": [Config.SERVER_URL],
            "scopes_supported": Config.SUPPORTED_SCOPES,
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{Config.SERVER_URL}/docs"
        }

    # Dynamic Client Registration (RFC 7591)
    @router.post("/register")
    async def register_client(request: Request):
        """Dynamic Client Registration endpoint"""
        try:
            data = await request.json()
        except:
            data = {}

        client_id = secrets.token_urlsafe(32)
        client_secret = secrets.token_urlsafe(32)

        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": data.get("client_name", "MCP Client"),
            "redirect_uris": data.get("redirect_uris", Config.DEFAULT_REDIRECT_URIS),
            "grant_types": data.get("grant_types", Config.DEFAULT_GRANT_TYPES),
            "scope": data.get("scope", Config.DEFAULT_SCOPE),
            "created_at": time.time()
        }

        # Store client in database
        db_manager.create_client(client_info)

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_info["client_name"],
            "redirect_uris": client_info["redirect_uris"],
            "grant_types": client_info["grant_types"],
            "scope": client_info["scope"]
        }

    # Authorization endpoint
    @router.get("/authorize")
    async def authorize(
        response_type: str,
        client_id: str,
        redirect_uri: str,
        scope: str = Config.DEFAULT_SCOPE.split()[0],  # Default to first scope
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ):
        """OAuth 2.1 Authorization endpoint"""

        # Validate client
        client = db_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client_id")

        # Validate redirect URI
        if redirect_uri not in client["redirect_uris"]:
            raise HTTPException(status_code=400, detail="Invalid redirect_uri")

        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)

        # Store authorization code with PKCE info
        code_data = {
            "code": auth_code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": time.time(),
            "expires_at": time.time() + (Config.AUTH_CODE_EXPIRES_MINUTES * 60)
        }
        db_manager.create_auth_code(code_data)

        # Build callback URL
        params = {"code": auth_code}
        if state:
            params["state"] = state

        callback_url = f"{redirect_uri}?{urlencode(params)}"
        return RedirectResponse(url=callback_url)

    # Token endpoint
    @router.post("/token")
    async def token_endpoint(
        grant_type: str = Form(...),
        client_id: str = Form(...),
        client_secret: str = Form(...),
        code: Optional[str] = Form(None),
        redirect_uri: Optional[str] = Form(None),
        code_verifier: Optional[str] = Form(None),
        refresh_token: Optional[str] = Form(None),
        scope: Optional[str] = Form(None)
    ):
        """OAuth 2.1 Token endpoint"""

        # Validate client credentials
        client = db_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client")

        if client["client_secret"] != client_secret:
            raise HTTPException(
                status_code=400, detail="Invalid client credentials")

        if grant_type == "authorization_code":
            return await _handle_authorization_code_grant(
                code, client_id, redirect_uri, code_verifier
            )
        elif grant_type == "client_credentials":
            return await _handle_client_credentials_grant(client_id, scope)
        elif grant_type == "refresh_token":
            return await _handle_refresh_token_grant(refresh_token, client_id)
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported grant type")

    # SSE endpoint for MCP communication
    @router.get("/sse")
    async def sse_endpoint(request: Request, current_user: dict = Depends(get_current_user)):
        """SSE endpoint for authenticated MCP communication"""
        async def event_stream():
            try:
                # Send initial connection event
                session_id = secrets.token_urlsafe(16)
                connection_data = {
                    'type': 'connection',
                    'session_id': session_id,
                    'user': current_user.get('sub'),
                    'scopes': current_user.get('scope', '').split()
                }
                yield f"data: {json.dumps(connection_data)}\n\n"

                # Keep connection alive
                import asyncio
                while True:
                    ping_data = {'type': 'ping', 'timestamp': time.time()}
                    yield f"data: {json.dumps(ping_data)}\n\n"
                    await asyncio.sleep(30)
            except Exception:
                pass

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Health check endpoint
    @router.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "mcp-video-transcriber"}

    return router

# Helper functions for token endpoint


async def _handle_authorization_code_grant(code: str, client_id: str, redirect_uri: str, code_verifier: str):
    """Handle authorization code grant flow"""
    if not code:
        raise HTTPException(
            status_code=400, detail="Invalid authorization code")

    auth_info = db_manager.get_auth_code(code)
    if not auth_info:
        raise HTTPException(
            status_code=400, detail="Invalid authorization code")

    # Check expiration
    if time.time() > auth_info["expires_at"]:
        db_manager.delete_auth_code(code)
        raise HTTPException(
            status_code=400, detail="Authorization code expired")

    # Validate PKCE if provided
    if auth_info.get("code_challenge"):
        if not code_verifier:
            raise HTTPException(
                status_code=400, detail="Code verifier required")

        if auth_info["code_challenge_method"] == "S256":
            verifier_hash = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
            if verifier_hash != auth_info["code_challenge"]:
                raise HTTPException(
                    status_code=400, detail="Invalid code verifier")

    # Generate tokens
    scopes = auth_info["scope"].split()
    access_token = create_access_token(client_id, scopes)
    refresh_token_value = secrets.token_urlsafe(32)

    # Store refresh token
    token_data = {
        "token": refresh_token_value,
        "client_id": client_id,
        "scope": auth_info["scope"],
        "created_at": time.time()
    }
    db_manager.create_refresh_token(token_data)

    # Clean up authorization code
    db_manager.delete_auth_code(code)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": Config.JWT_EXPIRES_MINUTES * 60,
        "refresh_token": refresh_token_value,
        "scope": auth_info["scope"]
    }


async def _handle_client_credentials_grant(client_id: str, scope: str):
    """Handle client credentials grant flow"""
    request_scope = scope or Config.DEFAULT_SCOPE.split()[
        0]  # Default to first scope
    scopes = request_scope.split()

    access_token = create_access_token(client_id, scopes)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": Config.JWT_EXPIRES_MINUTES * 60,
        "scope": request_scope
    }


async def _handle_refresh_token_grant(refresh_token: str, client_id: str):
    """Handle refresh token grant flow"""
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    token_info = db_manager.get_refresh_token(refresh_token)
    if not token_info:
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    if token_info["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    # Generate new access token
    scopes = token_info["scope"].split()
    access_token = create_access_token(client_id, scopes)
    new_refresh_token = secrets.token_urlsafe(32)

    # Update refresh token
    db_manager.delete_refresh_token(refresh_token)
    new_token_data = {
        "token": new_refresh_token,
        "client_id": client_id,
        "scope": token_info["scope"],
        "created_at": time.time()
    }
    db_manager.create_refresh_token(new_token_data)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": Config.JWT_EXPIRES_MINUTES * 60,
        "refresh_token": new_refresh_token,
        "scope": token_info["scope"]
    }
