Working_OPC (open62541 + Process Simulate)
=========================================

Server endpoint:
  opc.tcp://127.0.0.1:4841

Main NodeId (Boolean):
  ns=1;s=PS.Enabled
Browse path:
  Objects -> PS -> Enabled

Run server (portable):
  server_json_config.exe "ps_server.json5"

Files included:
- ps_server.json5 (server config)
- server_json_config.c (server source)
- open62541_server_cert.der (server certificate)
- open62541_server_key.pem (private key)
- open62541_pki\ (PKI trust folder)
