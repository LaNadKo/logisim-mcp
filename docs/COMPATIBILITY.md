# Compatibility and validation

Version: **1.0.0**. Portable runtimes: CPython 3.13.15 and Temurin JDK 17.0.20.1+1. Target application: **classic Logisim 2.7.1 only**.

## Platform matrix

| Platform | Runtime archives | Validation before publication |
|---|---|---|
| Windows x64 | Included | Passed locally and on `windows-latest` |
| Linux x64 | Included | Passed in a local Ubuntu 24.04/Xvfb container and on `ubuntu-24.04` |
| Linux ARM64 | Included | Passed on `ubuntu-24.04-arm` |
| macOS Intel | Included | Passed on `macos-15-intel` |
| macOS Apple Silicon | Included | Passed on `macos-15` |

The release acceptance suite runs on all five targets: 12 portable unit checks, 5 dependency-path regression checks, 3 stdio guidance tests, 77 core live scenarios, 13 extended scenarios and 7 native smoke checks. Windows-specific path tests are skipped on other systems; the directory-link test requires OS permission to create a link. Each runner copies the package into a fresh directory containing spaces, Cyrillic and CJK characters, extracts its bundled runtimes, rebuilds the Java agent, launches the native GUI and verifies explicit dynamic attach to the managed JVM. System Python/Java settings are removed from the child environment; the system Python used to prepare the CI copy is not a portable runtime dependency. Check the [Actions run for the tagged commit](https://github.com/LaNadKo/logisim-mcp/actions/workflows/portable.yml) for the current release's result.

The [portable CI workflow](https://github.com/LaNadKo/logisim-mcp/actions/workflows/portable.yml) reports current results separately for all five targets. A successful run is evidence for that runner's OS version and scenario, not every physical device or GUI configuration.

## Host requirements

- Windows 10 version 1903 or later / Windows 11 x64, built-in Windows PowerShell and `tar.exe`; a writable, user-private directory. A private launcher copy enables the Windows UTF-8 process manifest for Unicode paths; see [third-party modifications](../THIRD_PARTY_NOTICES.md).
- Linux x64/ARM64 with glibc and a graphical X11/XWayland session. Ubuntu 24.04 was used for local testing. A minimal container needs `xvfb`, `xauth`, `libxrender1`, `libxtst6`, `libxi6`, `libfreetype6`, `fontconfig`, `libasound2t64` and `libgtk-3-0` (distribution package names vary). Python/Java are bundled; these desktop/OS libraries are not.
- macOS Intel or Apple Silicon supported by the bundled Python and JDK; a logged-in desktop session. The bundle is not an Apple-notarized application. Apply your normal download verification and OS trust policy; no launcher disables Gatekeeper or changes quarantine settings.
- No support claim for native Windows ARM64, 32-bit systems, Alpine/musl, mobile OSes, Logisim Evolution or a headless GUI session without a display server.
- Universal archive needs roughly 1.2 GB before extraction and additional space for the current platform's JDK/Python. Only one platform is extracted at a time; it is safe to keep the other platform archives for later transfer.

## What is checked

- Protocol and guidance delivery, catalog/schema consistency, relative path behavior, dependency lock and bundled source provenance.
- Creating all 57 builtin component types and inspecting their native ports and attributes.
- Selected bus, RAM/ROM, native synthesis, clipboard, undo, hierarchy, appearance, logger, library and clock workflows.
- A fresh native AND circuit checked against an independent four-row truth table, saved and reopened, exported as a PNG, plus independent headless CLI and ten clock transitions.
- Unauthenticated HTTP bridge requests are rejected; typed file operations reject paths outside the workspace.

These checks do not cover every component state, arbitrary reflection calls, third-party JAR plugins, all printing dialogs or every host desktop setup. A discovered API signature is not a tested behavior. macOS-specific legacy menu integration can fall back to ordinary Swing menus.

## Troubleshooting

| Symptom | Action |
|---|---|
| Runtime archive missing | Download the universal release, or fetch pinned dependencies from the source checkout with Python 3.11+ |
| SHA-256 mismatch | Re-download the affected archive; do not bypass verification |
| MCP initialization times out | Run `doctor` first to finish runtime extraction; configure a 120-second startup timeout |
| Multiple matching JVMs | Use `attach --pid PID`, or use the bundle's managed `start` instance |
| Desktop not available | Start from a graphical session; use Xvfb only for a dedicated CI/test session |
| Attach unavailable | Use the bundled JDK, the same OS user and compatible target JVM; managed `start` avoids dynamic attach |
| Moved folder | Regenerate client configuration; update any custom absolute paths; reopen the managed Logisim from its new location |
| Old state after crash | Close only the failed managed test instance, then run `start` again; stale token/port state is authenticated before reuse |
| Unix extraction interrupted | Ensure no launcher is extracting, then remove the empty `.runtime/<platform>/bootstrap.lockdir` and retry |
