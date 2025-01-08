package aws_rego.rds_checks.empty_storage.empty_storage

import rego.v1

storage_instances contains instance if {
instance |
	some instance in input.rds_instances[_]
	instance.StorageUtilization < 40
}

# Combine results into a single report
details := {"empty_storage_instances": [instance | instance := storage_instances[_]]}
