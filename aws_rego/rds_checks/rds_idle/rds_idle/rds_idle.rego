package aws_rego.rds_checks.rds_idle.rds_idle

import rego.v1

underutilized_rds_instances contains instance if {
instance |
	some instance in input.rds_instances[_]
}

details := {"underutilized_rds_instances": [instance | instance := underutilized_rds_instances[_]]}
