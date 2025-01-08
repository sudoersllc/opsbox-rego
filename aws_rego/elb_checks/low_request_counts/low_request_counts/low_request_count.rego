package aws_rego.elb_checks.low_request_counts.low_request_counts

import rego.v1

# Define the threshold for underutilization
underutilization_threshold := 100

# Rule to identify underutilized ELBs
underutilized_elbs contains elb if {
elb |
	some elb in input.elbs[_]
	elb.RequestCount <= underutilization_threshold
}

# Collect the entire ELB object for all underutilized ELBs
underutilized_elb_details contains elb if {
elb |
	some elb in underutilized_elbs[_]
}

# Collect details of all underutilized ELBs
details := {"elbs": [elb | elb := underutilized_elb_details[_]]}
