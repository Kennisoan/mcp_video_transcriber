import httpx
from fastmcp import FastMCP
from config import Config

# Initialize FastMCP server
mcp = FastMCP("video_transcriber")


@mcp.tool
async def get_projects() -> str:
    """
    Get a list of projects with transcribed videos

    Returns:
        JSON string containing list of projects with their IDs and names
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.API_BASE_URL}/projects/")
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        return f"Network error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool
async def create_project(project_name: str) -> str:
    """
    Create a new project for organizing video transcripts

    Args:
        project_name: Name for the new project. Should be descriptive and meaningful.

    Returns:
        JSON string containing the created project details

    Hint: Ask the user for a meaningful project name that reflects the content theme.
    Don't use generic names like "Project 1" - make it contextual to their use case.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.API_BASE_URL}/projects/",
                json={"name": project_name}
            )
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        return f"Network error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool
async def get_video_transcripts(project_id: str) -> str:
    """
    Get all video transcripts for a specific project

    Args:
        project_id: The ID of the project to get videos from

    Returns:
        JSON string containing list of videos with their transcripts and metadata

    Hint: Use get_projects tool first to find the correct project_id and name.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.API_BASE_URL}/videos/?project_id={project_id}")
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        return f"Network error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool
async def transcribe_video(project_id: str, video_url: str) -> str:
    """
    Transcribe a YouTube video and add it to a project

    Args:
        project_id: The project ID to add the video to (use "1" as default if no specific project)
        video_url: Full YouTube URL (must start with https://www.youtube.com/watch?v=)

    Returns:
        JSON string containing the video object with initial status

    Important Notes:
    - If user doesn't specify a project, use project_id = "1" (default project)
    - If they want a specific project, use get_projects or create_project first
    - The video_url MUST be a complete YouTube URL starting with https://www.youtube.com/watch?v=
    - Video transcription happens asynchronously (takes about 1 minute)
    - Initial status will be "pending", check back later with get_video_transcripts
    - Video will be fully transcribed when status changes to "completed"
    """
    # Validate YouTube URL format
    if not video_url.startswith("https://www.youtube.com/watch?v="):
        return "Error: video_url must be a valid YouTube URL starting with https://www.youtube.com/watch?v="

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.API_BASE_URL}/videos/",
                json={
                    "project_id": project_id,
                    "link": video_url,
                    "status": "pending",
                    "chat_state": "initial"
                }
            )
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        return f"Network error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool
async def search_transcripts(query: str, project_id: str = None) -> str:
    """
    Search through video transcripts for specific content

    Args:
        query: Search terms to look for in transcripts
        project_id: Optional project ID to limit search scope

    Returns:
        JSON string containing matching videos and relevant transcript segments

    Note: This tool searches through the text content of all transcribed videos.
    """
    try:
        params = {"q": query}
        if project_id:
            params["project_id"] = project_id

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{Config.API_BASE_URL}/search/",
                params=params
            )
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        return f"Network error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"


def get_mcp_server():
    """Get the configured FastMCP server instance"""
    return mcp
