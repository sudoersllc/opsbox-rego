package aws_rego.elb_checks.inactive_load_balancers.inactive_load_balancers

import rego.v1

default allow := false

allow if {
elb |
	some elb in input.elbs
	elb.State == "active"
}

allow if {
elb |
	some elb in input.elbs
	elb.RequestCount <= input.elb_inactive_requests_threshold
}

details contains load_balancer if {
	some load_balancer in input.elbs
	load_balancer.State == "inactive"
}

details contains load_balancer if {
	some load_balancer in input.elbs
	load_balancer.RequestCount <= input.elb_inactive_requests_threshold
	load_balancer.State == "active"
}
