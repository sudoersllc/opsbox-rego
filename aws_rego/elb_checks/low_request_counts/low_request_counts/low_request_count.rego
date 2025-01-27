package aws_rego.elb_checks.low_request_counts.low_request_counts

import rego.v1

allow if {
elb |
	some elb in input.elbs
	elb.RequestCount <= input.elb_low_requests_threshold
}

details := [elb | some elb in input.elbs; elb.RequestCount <= input.elb_low_requests_threshold]
