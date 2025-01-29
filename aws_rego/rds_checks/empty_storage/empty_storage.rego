package aws_rego.rds_checks.empty_storage.empty_storage

import rego.v1

details := [instance | some instance in input.rds_instances; instance.StorageUtilization < input.rds_empty_storage_threshold]
