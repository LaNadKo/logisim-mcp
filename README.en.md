# ⚡ Logisim MCP – Live Circuit Design & Simulation

<div align="center">

[![Logisim](https://img.shields.io/badge/Logisim-2.7.1-black?style=flat-square)](https://www.cburch.com/logisim/)
[![Python](https://img.shields.io/badge/Python-3.13-black?style=flat-square&logo=python)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-17-black?style=flat-square&logo=openjdk)](https://adoptium.net/)
[![MCP](https://img.shields.io/badge/MCP-54_tools-black?style=flat-square)](docs/TOOLS.md)
[![License](https://img.shields.io/badge/License-GPL--2.0--or--later-black?style=flat-square)](LICENSE)
[![CI](https://github.com/LaNadKo/logisim-mcp/actions/workflows/portable.yml/badge.svg)](https://github.com/LaNadKo/logisim-mcp/actions/workflows/portable.yml)

**A local MCP server that lets AI agents build, inspect and test circuits in the real Logisim application. The portable release includes Logisim, Python and Java.**

[🇷🇺 Читать на русском](README.md) • [Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Compatibility](docs/COMPATIBILITY.md) • [Releases](https://github.com/LaNadKo/logisim-mcp/releases)

</div>

---

## 📖 Overview

Logisim MCP connects an AI client to **classic Logisim 2.7.1** through an in-process Java agent. Place real components, connect their ports, change input signals, inspect simulation results and save `.circ` projects. Edits appear in the open application and use its native circuit model and simulator.

This is an independent community project. **Logisim Evolution is not supported.** Bring your own stdio-capable MCP client and AI model; neither is included in the bundle.

## 🌟 Key Features

| Area | Capabilities |
| :--- | :--- |
| 🧩 Circuit editing | Components, attributes, wires, move/duplicate, selection and clipboard |
| 🔬 Simulation | Pins, multibit buses, net probes, clock ticks, reset and subcircuit states |
| 🧮 Analysis | Truth tables, Boolean expressions, SOP/POS minimization and circuit synthesis |
| 💾 Memory | RAM/ROM access, hex import/export and RLE |
| 📂 Projects | Open/save with backup, libraries, statistics and native PNG/GIF/JPEG exports |
| 🛠 Native API | Menus, Swing widgets, circuit appearance, discovered Java methods and fields |
| 📚 Reference | 129 bundled manual pages, Java source search, class index and agent instructions |

**54 tools · 131 resources · no pip dependencies.** [Tool catalog](docs/TOOLS.md) · [JSON schemas](tools.json)

### 🎓 Full implementations by default

The complete [agent guide](AGENT_GUIDE.md) is sent in the MCP initialization response. Agents must follow the assignment, reference layout and user edits. Compact substitutes, hidden implementation blocks and abbreviated reports require an explicit request or an agreed choice. Minimization required by the assignment remains allowed. Formulas, Karnaugh maps, circuit structure and report must describe the same implementation.

---

## 🚀 Quick Start

### 1. Download the portable release

Get **`logisim-mcp-1.0.0-universal.zip`** from [Releases](https://github.com/LaNadKo/logisim-mcp/releases). Extract the entire folder into a writable location. GitHub's automatic **Source code.zip does not include runtime archives**.

The universal release includes CPython 3.13.15, Temurin JDK 17.0.20.1+1 and Logisim 2.7.1. First launch verifies SHA-256 and extracts only the current platform's runtimes. Normal startup requires no Python/Java installation, pip, admin privileges or internet. A graphical desktop and host OS libraries are still required; see [compatibility](docs/COMPATIBILITY.md).

### 2. Open Logisim

**Windows 10/11 x64:** double-click `launch.cmd`, or run:

```powershell
.\launch.cmd doctor
.\launch.cmd start
```

**Linux / macOS:**

```sh
sh launch.sh doctor
sh launch.sh start
```

Save circuits inside `workspace/`. To open one immediately:

```sh
sh launch.sh start workspace/example.circ
```

### 3. Configure your MCP client

Generate configuration for the bundle's current location:

```powershell
.\launch.cmd config
.\launch.cmd config --format codex
```

```sh
sh launch.sh config
sh launch.sh config --format codex
```

Copy the generated JSON or TOML into your client's MCP settings. It starts the server with the `mcp` subcommand over stdio. After moving the folder, generate configuration again. Run `doctor` once before connecting the client so first-time extraction does not consume its initialization timeout.

### 4. Ask for a circuit

> Build a complete half-adder using AND, OR and NOT gates. Do not use XOR. Show the expressions, test all four input combinations and save the circuit in the workspace.

The agent starts with `projects` and uses the returned project reference. To attach to an existing classic Logisim JVM instead of a managed instance:

```sh
sh launch.sh attach --pid 12345
```

Without an explicit PID, attachment requires exactly one matching JVM owned by the same OS user. Managed `start` loads the agent at startup and avoids restrictions on dynamic JVM attachment.

---

## 🏗 Architecture

```mermaid
flowchart LR
    AI[AI / MCP client] <-->|stdio JSON-RPC| PY[Python MCP server]
    PY <-->|Authenticated loopback| AG[Java agent]
    AG <-->|Swing EDT / native API| LS[Logisim 2.7.1]
    LS --> FILE[workspace: circuits and exports]
```

```text
logisim-mcp/
├── launch.cmd / launch.ps1 / launch.sh   # Offline platform launchers
├── launcher.py / runtime.py             # Paths, diagnostics, client config
├── mcp_server.py / workbench.py          # MCP protocol and tools
├── AGENT_GUIDE.md                        # Instructions delivered to agents
├── lib/                                 # Selected agent and attach helper
├── vendor/                              # Logisim, provenance, JDK sources
├── runtime-archives/                    # Five Python/Java platform pairs
├── dependencies.lock.json               # Pinned versions and SHA-256
├── scripts/ / tests/                     # Packaging and verification
├── .runtime/                            # Extracted on first use
├── .state/                              # Private connection state and log
└── workspace/                           # User circuits and exports
```

## ⚙️ Configuration

Copy `config.example.json` to `config.local.json` only when overriding defaults. Relative paths resolve from the bundle, independent of the caller's working directory. Environment variables take precedence.

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `LOGISIM_MCP_WORKSPACE` | Typed file-tool workspace boundary | `workspace/` |
| `LOGISIM_MCP_STATE_DIR` | Local state and connection token | `.state/` |
| `LOGISIM_MCP_JAVA_HOME` | Alternative JDK 17+ | Bundled platform JDK |
| `LOGISIM_MCP_LOGISIM` | Compatible classic Logisim JAR | `vendor/logisim-2.7.1.jar` |
| `LOGISIM_MCP_PID` | Explicit JVM attach target | Single matching JVM |

Reconnect after changing the workspace so the Java agent receives the same boundary. Absolute paths in custom configuration need updating after relocation. Client configuration is printed, never installed silently.

## ✅ Compatibility & Verification

Runtime archives cover **Windows x64, Linux x64/ARM64 and macOS Intel/Apple Silicon**. Available binaries are not evidence of successful execution on every platform. See [the compatibility matrix](docs/COMPATIBILITY.md) for actual checks and remaining limitations.

- Classic combinational analysis supports up to eight one-bit inputs and outputs. Multibit buses use ordinary circuit tools.
- Component ports must be inspected before wiring; moving a component does not reroute wires.
- Attribute changes and structural edits must be separate batches.
- RAM is simulation state; use hex export to transfer it. ROM contents are saved in the project.
- Menu/widget actions can be asynchronous. A discovered Java signature is not a validated workflow.
- Linux needs a graphical session; CI uses Xvfb. The portable bundle does not contain an entire operating system.

## 🔐 Security

Use a trusted local MCP client. The bridge listens on loopback and authenticates with a random token. Typed file tools enforce a workspace boundary, but reflection APIs and native dialogs operate with your user permissions: **this is not a sandbox**. Read [SECURITY.md](SECURITY.md).

To share a used installation, run the allowlisted release packager. Do not indiscriminately ZIP connection state, user circuits or logs.

## 🧪 Development

```sh
git clone https://github.com/LaNadKo/logisim-mcp.git
cd logisim-mcp
python3 scripts/fetch_dependencies.py   # Python 3.11+, initial source setup
sh launch.sh build
sh launch.sh test
```

Git contains source, the selected agent, Logisim and documentation. Large runtime archives ship in the portable release. Use `fetch_dependencies.py --all` and `package_release.py` for a universal offline distribution. [Development and release instructions](CONTRIBUTING.md).

## 📄 License

Adapter code: [GPL-2.0-or-later](LICENSE). Logisim, Python and OpenJDK retain their respective licenses and notices. Source locations and redistribution details are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This project is not affiliated with the original Logisim authors.
