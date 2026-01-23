# Third-party notices

The project's own code is MIT-licensed (see [LICENSE](LICENSE)). It ships or depends on the following third-party software, which keeps its own license.

## Shipped in this repository

| Component | Where | License |
|---|---|---|
| [OpenSSL](https://www.openssl.org/) 3.6.0 | `server/libcrypto-3-x64.dll`, `server/libssl-3-x64.dll` and the same DLLs in `legacy/minimal_server/` | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| [open62541](https://github.com/open62541/open62541) | Compiled into `server/server_json_config.exe` and `legacy/minimal_server/server_json_config.exe` | [MPL-2.0](https://www.mozilla.org/MPL/2.0/); some plugins and examples CC0 |

`server/server_json_config.c` started from an open62541 example released under CC0 1.0.

The server is built from upstream open62541 commit `029465e5c13ef4d566f63b034ec2a99e0b66e829` with the patch in [third_party/patches](third_party/patches). See [third_party/README.md](third_party/README.md).

## Python dependencies

Installed with pip from [requirements.txt](requirements.txt), not shipped:

| Package | License |
|---|---|
| [asyncua](https://github.com/FreeOpcUa/opcua-asyncio) | LGPL-3.0 |
| [cryptography](https://github.com/pyca/cryptography) | Apache-2.0 or BSD-3-Clause |
| [PyInstaller](https://pyinstaller.org/) | GPL-2.0 with an exception that allows distributing the built EXE |

An EXE built with PyInstaller bundles Python and these packages. If you distribute one, include their license notices.
