#!/usr/bin/env python3
"""MCP Server für Claude Desktop - Greiner Portal"""
import asyncio
import sqlite3
import subprocess
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

BASE_DIR = Path('/opt/greiner-portal')
DB_PATH = BASE_DIR / 'data/greiner_controlling.db'

server = Server("greiner-portal")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_file",
            description="Datei aus dem Greiner Portal Projekt lesen",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relativer Pfad ab /opt/greiner-portal/ (z.B. docs/PROJECT_STATUS.md)"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="list_directory",
            description="Verzeichnis-Inhalt auflisten",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relativer Pfad ab /opt/greiner-portal/ (z.B. docs/)",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="shell_exec",
            description="Shell-Befehl im Projekt-Verzeichnis ausfuehren",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell-Befehl (z.B. git log --oneline -10)"
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="db_query",
            description="SQLite Query auf greiner_controlling.db ausfuehren (nur SELECT)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT Query"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_files",
            description="Dateien im Projekt nach Name oder Inhalt suchen",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Suchbegriff (grep-Pattern)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Dateiname-Pattern (z.B. *.py, *.md)",
                        "default": "*"
                    }
                },
                "required": ["pattern"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "read_file":
            path = BASE_DIR / arguments["path"]
            # Sicherheitscheck: nicht aus Projektverzeichnis ausbrechen
            path = path.resolve()
            if not str(path).startswith(str(BASE_DIR.resolve())):
                return [types.TextContent(type="text", text="FEHLER: Pfad ausserhalb des Projektverzeichnisses")]
            if not path.exists():
                return [types.TextContent(type="text", text=f"FEHLER: Datei nicht gefunden: {path}")]
            content = path.read_text(encoding='utf-8', errors='replace')
            # Limit auf 100k Zeichen
            if len(content) > 100000:
                content = content[:100000] + f"\n\n... [ABGESCHNITTEN bei 100k Zeichen, Gesamtlaenge: {len(content)}]"
            return [types.TextContent(type="text", text=content)]

        elif name == "list_directory":
            path = BASE_DIR / arguments.get("path", "")
            path = path.resolve()
            if not str(path).startswith(str(BASE_DIR.resolve())):
                return [types.TextContent(type="text", text="FEHLER: Pfad ausserhalb des Projektverzeichnisses")]
            if not path.exists():
                return [types.TextContent(type="text", text=f"FEHLER: Verzeichnis nicht gefunden: {path}")]
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for p in items:
                prefix = "[DIR] " if p.is_dir() else "[FILE]"
                size = ""
                if p.is_file():
                    s = p.stat().st_size
                    size = f" ({s:,} bytes)" if s < 1024*1024 else f" ({s/1024/1024:.1f} MB)"
                lines.append(f"{prefix} {p.name}{size}")
            return [types.TextContent(type="text", text="\n".join(lines) if lines else "(leer)")]

        elif name == "shell_exec":
            cmd = arguments["command"]
            # Gefaehrliche Befehle blocken
            blocked = ['rm -rf', 'mkfs', 'dd if=', ':(){', 'shutdown', 'reboot']
            if any(b in cmd for b in blocked):
                return [types.TextContent(type="text", text="FEHLER: Befehl aus Sicherheitsgruenden blockiert")]
            result = subprocess.run(
                cmd, shell=True, cwd=str(BASE_DIR),
                capture_output=True, text=True, timeout=30
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            output += f"\n[Exit Code: {result.returncode}]"
            return [types.TextContent(type="text", text=output.strip())]

        elif name == "db_query":
            query = arguments["query"].strip()
            if not query.upper().startswith("SELECT"):
                return [types.TextContent(type="text", text="FEHLER: Nur SELECT-Queries erlaubt")]
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            import json
            result = json.dumps(rows, indent=2, default=str, ensure_ascii=False)
            if len(result) > 100000:
                result = result[:100000] + f"\n\n... [ABGESCHNITTEN, {len(rows)} Zeilen total]"
            return [types.TextContent(type="text", text=f"{len(rows)} Ergebnisse:\n{result}")]

        elif name == "search_files":
            pattern = arguments["pattern"]
            file_pattern = arguments.get("file_pattern", "*")
            cmd = f'grep -rl --include="{file_pattern}" "{pattern}" . 2>/dev/null | head -30'
            result = subprocess.run(
                cmd, shell=True, cwd=str(BASE_DIR),
                capture_output=True, text=True, timeout=15
            )
            return [types.TextContent(type="text", text=result.stdout.strip() or "Keine Treffer")]

        else:
            return [types.TextContent(type="text", text=f"Unbekanntes Tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"FEHLER: {type(e).__name__}: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
