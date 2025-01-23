package aws_rego.elb_checks.inactive_load_balancers.inactive_load_balancers

import rego.v1

default allow := false


details contains load_balancer if {
	some load_balancer in input.elbs
	load_balancer.State == "inactive"
}

details contains load_balancer if {
	some load_balancer in input.elbs
	load_balancer.RequestCount == 0
	load_balancer.State == "active"
}
