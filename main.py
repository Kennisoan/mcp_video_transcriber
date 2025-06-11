from typing import Any
import os
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("video_transcriber")
API_BASE_URL = os.getenv("API_BASE_URL").rstrip("/")


@mcp.tool()
async def get_projects() -> str:
    """Get a list of projects with transcribed videos"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/projects/")
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Request error: {e}"


@mcp.tool()
async def create_project(project_name: str) -> str:
    """
    Create a new project
    Hint: ask the user before naming the project, don't use generic project names, come up with the name from the context of the conversation or use the user's name.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/api/projects/", json={"name": project_name})
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Request error: {e}"


@mcp.tool()
async def get_video_transcripts(project_id: str) -> str:
    """
    Get a list of video transcripts for a project
    Hint: You can get all projects with their names and ids using get_projects tool.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/videos/?project_id={project_id}")
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Request error: {e}"


@mcp.tool()
async def transcribe_video(project_id: str, video_url: str) -> str:
    """
    Transcribe a video.
    Hints:
    - This tool will add a video to the project, and it will be transcribed asynchronously.
    - If the user does not specify they want to add a video to an existing project or create a new one, use project_id = 1. If they explicitly do — use respective tools to get a project_id.
    - The video_url must be a full valid youtube video url that begins with https://www.youtube.com/watch?v=
    - The tool will return the video object with it's status immediately. If the video is in the processing status, you can check back on it later by using get_video_transcripts tool with the same project_id (find the needed video in the response by it's id). The video will be transcribed in about a minute.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/videos/",
                json={
                    "project_id": project_id,
                    "link": video_url,
                    "status": "pending",
                    "chat_state": "initial"
                }
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Request error: {e}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
