# OPC UA server

An [open62541](https://www.open62541.org/)-based OPC UA server that acts as the signal bus between Process Simulate and the Python tools. This folder is self-contained: copy it to another PC to run the server there without build tools (see [docs/deployment.md](../docs/deployment.md)).

## Contents

| File | Purpose |
|---|---|
| `server_json_config.c` | Server source. Edit it to add or change variables. |
| `ps_server.json5` | Endpoint, application URI and security settings |
| `server_json_config.exe` | Prebuilt server |
| `libcrypto-3-x64.dll`, `libssl-3-x64.dll` | OpenSSL runtime |
| `open62541_server_cert.der`, `open62541_server_key.pem` | Server certificate and private key (machine-specific, git-ignored) |
| `open62541_pki/` | Certificate trust store (created on start, git-ignored) |
| `run_server.bat` | Starts the server from this folder |
| `setup_new_pc.ps1` | Writes this PC's hostname and IP into the config and generates a new certificate |
| `generate_cert.py` | Generates a certificate and key for a given hostname and IP |
| `build.ps1` | Rebuilds `server_json_config.exe` from `server_json_config.c` |

## Run

```powershell
.\run_server.bat
```

or, from this folder:

```powershell
.\server_json_config.exe ps_server.json5
```

Start the server from this folder, because the certificate, key and PKI paths are relative. `run_server.bat` changes to this folder first, so you can start it from anywhere.

The default endpoint is `opc.tcp://127.0.0.1:4841`. Run `setup_new_pc.ps1` to switch to this PC's network address. The variables the server creates are listed under [Address space](../docs/architecture.md#address-space).

To accept clients from other machines, open the port once in an elevated PowerShell:

```powershell
New-NetFirewallRule -DisplayName "OPC UA 4841" -Direction Inbound -LocalPort 4841 -Protocol TCP -Action Allow
```

## Add or change variables

1. Edit `server_json_config.c`. Each variable is a value, a `UA_VariableAttributes` block and a `UA_Server_addVariableNode` call. For example, a Boolean in the `Trigger` folder:

   ```c
   UA_Boolean myFlagValue = false;
   UA_VariableAttributes myFlagAttr = UA_VariableAttributes_default;
   myFlagAttr.displayName = UA_LOCALIZEDTEXT("en-US", "MyFlag");
   myFlagAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
   UA_Variant_setScalar(&myFlagAttr.value, &myFlagValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
   myFlagAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
   myFlagAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
   UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.MyFlag"),
                             triggerFolderId, UA_NS0ID(ORGANIZES),
                             UA_QUALIFIEDNAME(1, "MyFlag"),
                             UA_NS0ID(BASEDATAVARIABLETYPE),
                             myFlagAttr, NULL, NULL);
   ```

   Use `folderId` (PS), `triggerFolderId`, `feedbackFolderId` or a robot folder such as `robot1FolderId` as the parent. For other types, change the C type and the type constant:

   | C type | Type constant | Example initial value |
   |---|---|---|
   | `UA_Boolean` | `UA_TYPES_BOOLEAN` | `false` |
   | `UA_Int32` | `UA_TYPES_INT32` | `0` |
   | `UA_Double` | `UA_TYPES_DOUBLE` | `0.0` |
   | `UA_String` | `UA_TYPES_STRING` | `UA_STRING("Hello")` |

   The other scalar types follow the same pattern (`UA_SByte`/`UA_TYPES_SBYTE`, `UA_Byte`, `UA_Int16`, `UA_UInt16`, `UA_UInt32`, `UA_Int64`, `UA_UInt64`, `UA_Float`).

   Always set `dataType`. Without it, clients such as UaExpert show *DataType is Null*.

2. Rebuild with `.\build.ps1`.
3. Restart the server and refresh the address space in your client.
4. If the sequencer or Process Simulate should use the new node, update them too (see [Adapt it to your study](../README.md#adapt-it-to-your-study)).

## Build

```powershell
.\build.ps1
```

The script:

1. stops a running `server_json_config.exe`,
2. copies `server_json_config.c` to `third_party/open62541/examples/`,
3. configures CMake (`-A x64 -DUA_BUILD_EXAMPLES=ON`, plus `-DUA_ENABLE_ENCRYPTION_OPENSSL=ON` when OpenSSL is found) if the build folder is missing or was configured for another path,
4. builds the `server_json_config` target in Release and copies the EXE back here,
5. copies the OpenSSL DLLs here if they are missing.

The pinned open62541 version treats `UA_ENABLE_ENCRYPTION_OPENSSL` as deprecated and builds without encryption unless `UA_ENABLE_ENCRYPTION` is set. Use `-DUA_ENABLE_ENCRYPTION=OPENSSL` (manual build below) to enable the security policies in `ps_server.json5`.

### Requirements

- open62541 source in `third_party/open62541` (see [third_party/README.md](../third_party/README.md))
- CMake, found on `PATH`, in a standard install folder or through `CMAKE_PATH`
- Visual Studio 2022 Build Tools with the C++ workload (MSBuild is located with `vswhere`)
- OpenSSL for Windows x64, found on `PATH`, in a standard install folder or through `OPENSSL_DIR` (the folder that contains the DLLs)

If MSBuild still isn't found, run `build.ps1` from **Developer PowerShell for VS 2022**.

### Manual build

```powershell
Copy-Item -Force server_json_config.c ..\third_party\open62541\examples\
cmake -S ..\third_party\open62541 -B ..\third_party\open62541\build -A x64 -DUA_BUILD_EXAMPLES=ON -DUA_ENABLE_ENCRYPTION=OPENSSL
cmake --build ..\third_party\open62541\build --config Release --target server_json_config
Copy-Item -Force ..\third_party\open62541\build\bin\examples\server_json_config.exe .
```

## Configuration

`ps_server.json5`:

| Setting | Default | Notes |
|---|---|---|
| `applicationUri` | `urn:opcua-ps-server:open62541:ps` | Must match the URI in the certificate |
| `discoveryUrls`, `serverUrls` | `opc.tcp://127.0.0.1:4841` | Address clients connect to and the server listens on |
| `securityPolicies` | None, Basic256Sha256, Aes128_Sha256_RsaOaep, Aes256_Sha256_RsaPss | Only used by a build with encryption |
| `pkiFolder` | `./open62541_pki` | Trust store, only used by a build with encryption |

`setup_new_pc.ps1` rewrites the URI and URLs and regenerates the certificate. To do it by hand, see [docs/deployment.md](../docs/deployment.md#manual).

## Troubleshooting

| Symptom | Check |
|---|---|
| Config or certificate errors on start | Start from this folder or use `run_server.bat`. On a fresh checkout, run `setup_new_pc.ps1` to create the certificate and key. |
| `Field name 'securityPolicies' unknown` | Expected with the prebuilt EXE, which has no encryption support. See [Build](#build). |
| New variable missing | `build.ps1` finished without errors, the EXE timestamp changed, the server was restarted and the client refreshed. |
| *DataType is Null* in UaExpert | Set `dataType` on the variable attributes. |
| Process Simulate can't connect | The IP in the config is this PC's address on that network, the certificate matches the current hostname and IP, and port 4841 is open. |
