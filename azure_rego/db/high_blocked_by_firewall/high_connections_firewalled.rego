package azure_rego.db.high_connections_failed

import rego.v1

details := [server | some server in input.azure_sql_dbs; server.connection_failed <= input.connections_failed_upper_bound]
