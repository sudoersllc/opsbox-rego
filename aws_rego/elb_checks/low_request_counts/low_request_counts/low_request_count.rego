package aws.cost.low_request_count

# Define the threshold for underutilization
underutilization_threshold := 100

# Rule to identify underutilized ELBs
underutilized_elbs[elb] {
    elb := input.elbs[_]
    elb.RequestCount <= underutilization_threshold
}

# Collect the entire ELB object for all underutilized ELBs
underutilized_elb_details[elb] {
    elb := underutilized_elbs[_]
}

# Collect details of all underutilized ELBs
details := {"elbs": [elb | elb := underutilized_elb_details[_]]}
