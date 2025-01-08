package aws_rego.elb_checks.high_error_rate.high_error_rate

import rego.v1

allow if {
	elb |
		some elb in input.elbs
		elb.ErrorRate > 5
}

details := [elb | some elb in input.elbs; elb.ErrorRate > 1]
