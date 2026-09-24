# Development

Use Python 3.11+ and a JDK 17+, or the runtimes in a portable release. No pip packages are required by the MCP server.

```sh
python3 scripts/fetch_dependencies.py
sh launch.sh build
sh launch.sh test
sh launch.sh start
.runtime/linux-x64/python/python/bin/python3 scripts/smoke_live.py
```

Windows equivalents use `launch.cmd` and `.runtime\windows-x64\python\python\python.exe`.

`test_live.py` exercises all 57 component factories and 77 core scenarios. `test_extended.py` exercises 13 additional native API scenarios. Run them only against a dedicated test JVM launched with this bundle; they create test projects, generate files in the workspace and touch the native clipboard. `scripts/smoke_live.py` closes only the scratch projects it created. Do not treat these suites as exhaustive verification of every component state.

When modifying Java, run `build` before live tests. Agent jars are versioned by a hash of all agent/helper Java sources, and `build-info.json` stores a relative path to the selected one. Reconnect only after preserving unsaved work. Regenerate `tools.json` when tool descriptions or schemas change.

For release preparation:

```sh
python3 scripts/fetch_dependencies.py --all
python3 scripts/package_release.py
python3 scripts/verify_release.py dist/logisim-mcp-1.0.0-universal.zip
```

The source repository excludes runtime archives, extracted runtimes, user projects and connection state. The release package adds pinned runtime archives and corresponding OpenJDK sources. Version and architecture support are defined in `runtime.py` and `dependencies.lock.json`. Update compatibility evidence honestly when changing either.
