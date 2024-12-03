package aws.cost.high_error_rate

import future.keywords.in

# Rule to identify ELBs with high error rates
high_error_rate_elbs[elb] {
    elb := input.elbs[_]
    elb.ErrorRate > 5  # Threshold for high error rate in percentage
}

# Collect details of all ELBs with high error rates
details := {elb | high_error_rate_elbs[elb]}

# Entry point for OPA to evaluate
default allow = false

allow {
    count(details) > 0
}