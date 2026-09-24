# Security model

This is a local desktop automation bridge for trusted MCP clients. It runs with the current user's privileges and can modify the open Logisim project.

- MCP uses stdio. The Java bridge binds only to `127.0.0.1`, uses a random per-connection bearer token and accepts only authenticated POST requests.
- Token/state files live in `.state/`, are excluded from releases and Git, and use owner-only modes on Unix. On Windows they inherit the extraction directory's ACL: place the bundle in a directory private to your user.
- The agent receives startup options through a temporary local file, avoiding tokens in process command lines. Runtime downloads are explicit, pinned and SHA-256 checked. Normal portable startup performs no download.
- Typed file tools enforce the configured workspace boundary. General Java reflection APIs and native file dialogs are privileged escape hatches; **this MCP is not a sandbox**. Use OS-level isolation if clients or prompts are untrusted.
- Imported project files, third-party JAR libraries and external documentation are untrusted input. Do not load unknown executable libraries merely because an agent suggests doing so.
- Workspaces, exports and signal logs can contain personal or proprietary information. Before sharing a used folder, create a clean release with `scripts/package_release.py`; do not ZIP the working directory indiscriminately.
- Do not expose the bridge through a reverse proxy, LAN bind or tunnel. No remote authentication/authorization scheme is provided.

Report suspected vulnerabilities privately through [GitHub's security reporting](https://github.com/LaNadKo/logisim-mcp/security/advisories/new) when available. If unavailable, open an issue requesting a private contact without posting credentials, sensitive circuits or an exploit against somebody else's machine.
