package aws_rego.elb_checks.inactive_load_balancers.inactive_load_balancers

import rego.v1

# Rule to identify inactive ELBs based on instance health
inactive_elbs contains elb if {
elb |
	some elb in input.elbs
	# health |
	# some health in elb.InstanceHealth
	# "unhealthy" in health.State # Third condition
}

# Collect details of all inactive ELBs (return the entire elb object)

# Create a details object to return all inactive ELBs
details := {"elbs": [elb | elb := inactive_elb_details[_]]}
