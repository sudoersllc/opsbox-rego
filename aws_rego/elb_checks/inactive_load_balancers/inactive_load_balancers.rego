package aws.cost.inactive_load_balancers

# Rule to identify inactive ELBs based on instance health
inactive_elbs[elb] {
    elb := input.elbs[i]
    # Check if any instance for this ELB is in an inactive state
    health := elb.InstanceHealth[_]
    health.State == "unused"  # First condition
}

inactive_elbs[elb] {
    elb := input.elbs[i]
    health := elb.InstanceHealth[_]
    health.State == "stopped"  # Second condition
}

inactive_elbs[elb] {
    elb := input.elbs[i]
    health := elb.InstanceHealth[_]
    health.State == "unhealthy"  # Third condition
}

# Collect details of all inactive ELBs (return the entire elb object)
inactive_elb_details[elb] {
    elb := inactive_elbs[_]
}

# Create a details object to return all inactive ELBs
details := {"elbs": [elb | elb := inactive_elb_details[_]]}
