# Third-party components

Logisim Live MCP's adapter source is provided under **GPL-2.0-or-later**; see [LICENSE](LICENSE). It interfaces with classic Logisim and is not an official Carl Burch or Logisim Evolution release. Bundled dependencies retain their own licenses and copyright notices.

| Component | Version | License and source |
|---|---|---|
| Classic Logisim | 2.7.1 | GPL-2.0-or-later, Carl Burch and contributors. [Upstream](https://sourceforge.net/projects/circuit/files/2.7.x/2.7.1/), [license](licenses/Logisim-COPYING.txt). Java source is included under `src/` inside `vendor/logisim-2.7.1.jar`. |
| Eclipse Temurin OpenJDK | 17.0.20.1+1 | GPL-2.0 with Classpath Exception plus bundled component notices. Each original JDK archive retains `legal/`; complete matching OpenJDK source archive is included under `vendor/sources/` in the portable release. [Upstream release](https://github.com/adoptium/temurin17-binaries/releases/tag/jdk-17.0.20.1%2B1). |
| CPython via python-build-standalone | 3.13.15 / 20260901 | Python Software Foundation License and licenses of included dependencies. Each original archive retains `python/LICENSE.txt` and component notices. [Distribution release](https://github.com/astral-sh/python-build-standalone/releases/tag/20260901), [CPython source](https://www.python.org/downloads/release/python-31315/). |

The Logisim JAR contains the unchanged entries of the upstream Windows executable's ZIP payload, repacked without its Windows launcher stub. `vendor/logisim-provenance.json` records the original and repacked SHA-256 values. The Java classes, bundled source and manual are unchanged.

`dependencies.lock.json` records exact runtime download URLs, sizes and SHA-256 values for each OS/CPU pair. `scripts/fetch_dependencies.py` retrieves the pinned artifacts, including the corresponding OpenJDK sources. The universal release includes those original archives without removing license files. Do not remove the source archive or license notices when redistributing this bundle.

The runtime distributors' source/build instructions are available in [python-build-standalone](https://github.com/astral-sh/python-build-standalone) and [Temurin build](https://github.com/adoptium/temurin-build). The MCP agent and launcher build source and scripts are included in this repository and every portable release.

On Windows, `windows_utf8.py` creates a private `java-logisim-utf8.exe` (and `javac-logisim-utf8.exe` when building) beside the extracted vendor launcher. The copy adds `activeCodePage=UTF-8` to its application manifest so JDK 17 can find its DLLs under Unicode paths. Original executables and dependency archives remain unchanged. Derived copies have different hashes and do not retain a valid vendor Authenticode signature; they are local build products, not vendor-signed binaries. The complete transformation source is included. This changes the copied process's encoding only, without changing Windows locale, registry or trust settings. Windows 10 version 1903 or later is required.
