FROM python:3.12-slim-bookworm

# Copy uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync --frozen

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables for production deployment
ENV HOST=0.0.0.0
ENV PORT=8000
ENV SERVER_URL=http://localhost:8000

# Expose port 8000 for the OAuth-enabled MCP server
EXPOSE 8000

# Create volume for database persistence
VOLUME ["/app/data"]

# Run the OAuth-enabled MCP server
CMD ["uv", "run", "main.py"] 