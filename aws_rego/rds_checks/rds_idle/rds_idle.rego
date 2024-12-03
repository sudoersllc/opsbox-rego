package aws.cost.rds_idle
underutilized_rds_instances[instance] {
    instance := input.rds_instances[_]
}

details := {
    "underutilized_rds_instances": [instance | instance := underutilized_rds_instances[_]],
}
