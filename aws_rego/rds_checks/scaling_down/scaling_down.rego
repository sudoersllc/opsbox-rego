package aws.cost.scaling_down


recommendations_for_scaling_down[recommendation] {
    instance := input.rds_instances[_]
    instance.CPUUtilization < 20  # Example threshold for scaling down
    current_instance_type := instance.InstanceType

    # Example logic to determine a smaller instance type
    # This should be customized based on available instance types and their performance characteristics
    smaller_instance_type := {
        "db.m5.large": "db.m5.medium",
        "db.m5.xlarge": "db.m5.large",
        "db.r5.large": "db.r5.medium",
        "db.r5.xlarge": "db.r5.large"
    }[current_instance_type]

    recommendation := {
        "InstanceIden"
        "SuggestedInstanceType": smaller_instance_type
    }
}

# Combine recommendations into a single report
details := {
    "recommendations_for_scaling_down": [recommendation | recommendation := recommendations_for_scaling_down[_]],
}   