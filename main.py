"""
MCP Video Transcriber Server - Main Application

Clean, production-ready FastAPI application with proper separation of concerns.
This file only handles app setup, routing, and middleware configuration.
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from oauth import create_oauth_router
from mcp_server import get_mcp_server

# Initialize FastAPI application
app = FastAPI(
    title="MCP Video Transcriber",
    description="OAuth 2.1 compliant MCP server for video transcription",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(CORSMiddleware, **Config.get_cors_settings())

# Include OAuth router (all OAuth endpoints)
oauth_router = create_oauth_router()
app.include_router(oauth_router)

# Handle 401 errors with proper WWW-Authenticate header


@app.exception_handler(401)
async def auth_exception_handler(request: Request, exc: HTTPException):
    """Handle 401 errors with proper WWW-Authenticate header"""
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
        headers={
            "WWW-Authenticate": f'Bearer resource="{Config.SERVER_URL}/.well-known/oauth-protected-resource"'
        }
    )

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "MCP Video Transcriber",
        "version": "2.0.0",
        "oauth_discovery": f"{Config.SERVER_URL}/.well-known/oauth-authorization-server",
        "documentation": f"{Config.SERVER_URL}/docs",
        "mcp_endpoint": f"{Config.SERVER_URL}/sse"
    }

# Application startup


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print(f"🚀 MCP Video Transcriber starting up...")
    print(f"📍 Server URL: {Config.SERVER_URL}")
    print(f"📊 API Base URL: {Config.API_BASE_URL}")
    print(
        f"🔐 OAuth Discovery: {Config.SERVER_URL}/.well-known/oauth-authorization-server")
    print(f"📡 MCP SSE Endpoint: {Config.SERVER_URL}/sse")
    print(f"📖 Documentation: {Config.SERVER_URL}/docs")

    # Initialize MCP server
    mcp_server = get_mcp_server()
    tools = await mcp_server.get_tools()
    print(f"🛠️  MCP Tools registered: {len(tools)}")
    for tool in tools:
        # Tools may be strings or objects, handle both cases
        if hasattr(tool, 'name'):
            print(f"   - {tool.name}: {tool.description}")
        else:
            print(f"   - {tool}")

    # Database cleanup
    from database import db_manager
    expired_count = db_manager.cleanup_expired_codes()
    if expired_count > 0:
        print(f"🧹 Cleaned up {expired_count} expired authorization codes")

    stats = db_manager.get_stats()
    print(f"📊 Database stats: {stats}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    print("🛑 MCP Video Transcriber shutting down...")

# Development server runner


def run_server():
    """Run the development server"""
    print(f"🔧 Starting development server...")
    print(f"🌐 Host: {Config.HOST}:{Config.PORT}")
    print(f"📁 Working directory: {os.getcwd()}")

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_server()
