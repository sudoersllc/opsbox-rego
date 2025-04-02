package azure_rego.db.high_cpu_percent

import rego.v1

details := [server | some server in input.azure_sql_dbs; server.cpu_percent >= input.cpu_upper_bound_threshold]
