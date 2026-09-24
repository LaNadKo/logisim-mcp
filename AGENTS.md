# Working on Logisim Live MCP

Read [AGENT_GUIDE.md](AGENT_GUIDE.md) before using this server to modify circuits. Full requested implementations are the default; no unrequested compact substitutes. Required minimization is allowed.

- Keep runtime paths relative to the package. Do not introduce machine-specific paths, Python packages, a global Java requirement or automatic downloads into the offline launcher.
- Preserve 54 tool capabilities and the existing native semantics. Add or change a schema together with `tools.json` and meaningful tests.
- Tokens, local state, circuits in `workspace/`, user documents and historical debug evidence must never enter Git or a release. Use the release script's allowlist.
- Use `launch.cmd test` / `sh launch.sh test` and `scripts/smoke_live.py` against a dedicated managed JVM. Live suites create scratch projects; never run them against a user's only unsaved project without preserving it.
- Java source changes require `launch ... build`. The build id covers all four agent/helper sources. Never overwrite a loaded agent JAR; old build ids remain distinct.
- Keep bundled third-party licenses and source archives. Pin dependencies by URL, size and SHA-256 in `dependencies.lock.json`.
- Document tested platforms separately from platforms for which binaries merely exist. Do not claim every native method or component state has been tested.
- Release packaging must include `AGENT_GUIDE.md`, native sources, dependency provenance and source archives. Do not publish local connection state or absolute author paths.
