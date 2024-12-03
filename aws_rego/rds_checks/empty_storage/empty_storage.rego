package aws.cost.empty_storage

empty_storage_instances[instance] {
    instance := input.rds_instances[_]
    instance.StorageUtilization < 40
}

# Combine results into a single report
details := {
    "empty_storage_instances": [instance | instance := empty_storage_instances[_]],
}
