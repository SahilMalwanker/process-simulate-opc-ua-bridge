# Contributing

Bug reports, ideas and pull requests are welcome.

## Set up

1. Install Python 3. To rebuild the server you also need the tools listed in [server/README.md](server/README.md#requirements).
2. Install the Python dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Configure the server for your PC:

   ```powershell
   .\server\setup_new_pc.ps1
   ```

## Checks

Run the same checks as CI before you open a pull request:

```powershell
py -m compileall -q client server legacy
foreach ($file in Get-ChildItem server -Filter *.ps1) {
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$null, [ref]$errors) | Out-Null
    if ($errors) { $errors; break }
}
```

To check that every node of the sequence resolves without writing anything, run the sequencer against a running server:

```powershell
py client\opcua_sequencer.py --once --dry-run
```

## Changing signals

Signals are defined in two places that must match:

- the nodes in `server/server_json_config.c` (rebuild with `server\build.ps1`),
- the steps in `OPERATION_GROUPS` in `client/opcua_sequencer.py`.

Update [docs/architecture.md](docs/architecture.md) if the address space or the handshake changes.

## Guidelines

- Keep each pull request focused on one change and describe how you tested it.
- Don't commit certificates, private keys or Process Simulate studies. They are git-ignored.
- Don't commit site-specific signal names, hostnames or IP addresses. Use generic examples such as `Feedback.Pick_Part_end` and `192.168.0.10`.
