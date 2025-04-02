package azure_rego.db.high_sessions_count

import rego.v1

details := [server | some server in input.azure_sql_dbs; server.sessions_count >= input.db_sessions_upper_bound]
