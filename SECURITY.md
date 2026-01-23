# Security

## Scope

The bridge is meant for trusted lab and engineering networks. Out of the box:

- the prebuilt server offers only the `None` security policy, because it is compiled without encryption,
- anonymous clients can connect,
- every client can read and write every variable.

## Hardening

- Listen only on the interface Process Simulate uses (`serverUrls` in `server/ps_server.json5`), and limit the firewall rule for port 4841 to the hosts that need it, for example with `New-NetFirewallRule -RemoteAddress`.
- Build the server with `-DUA_ENABLE_ENCRYPTION=OPENSSL` and remove the `None` policy if all your clients support encrypted policies.
- Keep `server/open62541_server_key.pem` private. It is git-ignored; if it was exposed, generate a new one with `server/setup_new_pc.ps1`.

## Reporting a vulnerability

Please report vulnerabilities privately through the repository's **Security → Report a vulnerability** form instead of a public issue. If the form isn't available, open an issue asking for a private contact, without any details of the vulnerability.
