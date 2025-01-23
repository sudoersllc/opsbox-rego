package aws_rego.elb_checks.high_error_rate.high_error_rate

import rego.v1


details := [elb | some elb in input.elbs; elb.ErrorRate > 1]
