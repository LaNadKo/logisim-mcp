"""Compatibility entry point; the current protocol lives in mcp_server.py."""
from mcp_server import serve
if __name__ == "__main__":
    serve()
