package aws_rego.rds_checks.empty_storage.empty_storage

import rego.v1

allow if {
instance |
	some instance in input.rds_instances
	instance.StorageUtilization < 40
}

details := [instance | some instance in input.rds_instances; instance.StorageUtilization < 40]
