package aws_rego.efs_checks.high_percentiolimit.high_percentiolimit

import rego.v1

default details := []

details := [efs | some efs in input.efss; efs.PercentIOLimit >= input.efs_percent_io_limit_threshold]
