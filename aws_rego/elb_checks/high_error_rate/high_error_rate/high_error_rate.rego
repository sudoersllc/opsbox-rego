package aws_rego.elb_checks.high_error_rate.high_error_rate

import rego.v1

# Rule to identify ELBs with high error rates
error_rate_elbs contains elb if {
elb |
	some elb in input.elbs[_]
	elb.ErrorRate > 5 # Threshold for high error rate in percentage
}

# Collect details of all ELBs with high error rates
details := [elb | some elb in error_rate_elbs[_]]

# Entry point for OPA to evaluate
default allow := false

allow if {
	count(details) > 0
}
