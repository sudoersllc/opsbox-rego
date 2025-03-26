package azure_rego.db.low_cpu_percent

import rego.v1

details := [server | some server in input.azure_sql_dbs; server.cpu_percent <= input.cpu_percent_threshold]
