package aws_rego.rds_checks.rds_idle.rds_idle

import rego.v1

# underutilized_rds_instances contains instance if {
# instance |
# 	some instance in input.rds_instances[_]
# }

allow if {
instance |
	some instance in input.rds_instances
	instance.CPUUtilization < 5
}

details := [instance | some instance in input.rds_instances; instance.CPUUtilization < 5]
