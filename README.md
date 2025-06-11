# MCP сервер для videogpt

### Доступные инструменты

### Установка:

1. Установите uv если он ещё не установлен:
   ```shell
   brew install uv
   ```
2. Добавьте конфигурацию (змените `/ABSOLUTE/PATH/TO/PARENT/FOLDER/` на настоящий путь к папке):
   ```json
    "mcpServers": {
      "Video Transcriber 🐉": {
        "command": "uv",
        "args": [
          "--directory",
          "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp_video_transcriber",
          "run",
          "main.py"
        ],
        "env": {
          "API_BASE_URL": "ссылка_на_апи"
        }
      },
      ...
    }
   ```
