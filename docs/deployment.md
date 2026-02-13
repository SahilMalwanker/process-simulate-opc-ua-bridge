# Deploying the server to another PC

The `server/` folder runs without build tools. The target PC only needs Python to generate its certificate.

## 1. Copy

Copy the whole `server/` folder. Optionally also copy `client/` and `requirements.txt` for the Python tools, and `third_party/open62541` if you need to rebuild on that PC.

## 2. Configure the PC

### Automatic

```powershell
cd server
.\setup_new_pc.ps1
```

The script:

1. reads the hostname and picks an IPv4 address (the first non-loopback, non-link-local address by interface index),
2. writes `urn:<hostname>:open62541:ps` and `opc.tcp://<ip>:4841` into `ps_server.json5`,
3. installs the Python `cryptography` package if needed and runs `generate_cert.py <hostname> <ip>`,
4. checks that the certificate, key and server EXE exist.

Check the IP it reports. On a PC with several network adapters (VPN, VM host-only network and so on) it may pick one Process Simulate can't reach. In that case, configure the PC manually.

If script execution is blocked, run `powershell -ExecutionPolicy Bypass -File .\setup_new_pc.ps1`.

### Manual

1. In `ps_server.json5`, replace the hostname and IP:

   ```json5
   applicationDescription: {
     applicationUri: "urn:TARGET_HOSTNAME:open62541:ps",
     // ...
     discoveryUrls: [
       "opc.tcp://TARGET_IP:4841"
     ]
   },

   serverUrls: [
     "opc.tcp://TARGET_IP:4841"
   ],
   ```

2. Generate a matching certificate and key. Run this from `server/`, because the script writes to the current folder:

   ```powershell
   py -m pip install cryptography
   py generate_cert.py TARGET_HOSTNAME TARGET_IP
   ```

The certificate is valid for 10 years and embeds the URI, hostname and IP. Regenerate it whenever any of these change.

## 3. Open the firewall port

Once per PC, in an elevated PowerShell:

```powershell
New-NetFirewallRule -DisplayName "OPC UA 4841" -Direction Inbound -LocalPort 4841 -Protocol TCP -Action Allow
```

## 4. Start and test

```powershell
.\run_server.bat
```

Connect UaExpert or Process Simulate to `opc.tcp://TARGET_IP:4841` and check that the `PS`, `Trigger` and `Feedback` folders appear under *Objects* (see the [address space](architecture.md#address-space)). If Process Simulate asks, trust the new server certificate.

## Troubleshooting

If Process Simulate rejects the connection, check that:

1. the IP in `ps_server.json5` is this PC's address on the network Process Simulate uses,
2. the certificate was regenerated after the last hostname or IP change,
3. Windows Firewall allows port 4841,
4. the server console shows no errors.

## Rebuilding on the target PC

You only need to rebuild to change variables. Copy `third_party/open62541` as well, install the build tools below, then run `server\build.ps1` (see [server/README.md](../server/README.md#build)).

- **Visual Studio 2022 Build Tools:** run `vs_BuildTools.exe` and select the *Desktop development with C++* workload, including MSVC v143 and a Windows 10/11 SDK. Reboot if asked.
- **CMake:** install the Windows x64 package from cmake.org and choose *Add CMake to the system PATH*. Check with `cmake --version`.
- **OpenSSL:** install a Win64 OpenSSL 3 build, for example to `C:\Program Files\OpenSSL-Win64`.
