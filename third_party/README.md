# Third-party code

## open62541

The server is built from [open62541](https://github.com/open62541/open62541) at commit `029465e5c13ef4d566f63b034ec2a99e0b66e829` (master, 2026-01-15). The source is only needed to rebuild the server. It lives in `third_party/open62541/`, which is git-ignored.

### Get the source

```powershell
git clone https://github.com/open62541/open62541.git third_party/open62541
git -C third_party/open62541 checkout 029465e5c13ef4d566f63b034ec2a99e0b66e829
git -C third_party/open62541 apply ../patches/open62541-client-endpoint-details.patch
```

Then run `server\build.ps1`. The build does not need the open62541 git submodules.

### Local changes

| File | Change |
|---|---|
| `examples/server_json_config.c` | Overwritten by `server/build.ps1` with `server/server_json_config.c` on every build. Edit the copy in `server/`. |
| `examples/client.c` | Accepts an endpoint URL and prints the security mode, policy and user tokens of each endpoint. Stored as [patches/open62541-client-endpoint-details.patch](patches/open62541-client-endpoint-details.patch). |

## License

open62541 is licensed under MPL-2.0; some plugins and examples are CC0. See `open62541/LICENSE` and `open62541/LICENSE-CC0`, and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
