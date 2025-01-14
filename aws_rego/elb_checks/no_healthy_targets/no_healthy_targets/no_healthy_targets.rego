package aws.cost.no_healthy_targets

import rego.v1

# # Rule to identify inactive ELBs based on instance health
# inactive_elbs[elb] {
#     elb := input.elbs[i]
#     # Check if any instance for this ELB is in an inactive state
#     health := elb.InstanceHealth[_]

default allow := false

allow if {
elb |
	some elb in input.elbs
}

# Create a details object to return all inactive ELBs
details contains elb if {
	some elb in input.elbs
	every instance in elb.InstanceHealth{
		instance.State == "unhealthy"
        }
}
