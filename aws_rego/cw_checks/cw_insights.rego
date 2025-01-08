package aws_rego.cw_checks

import rego.v1

default allow := false

metrics contains metric if {
	some metric in input.metrics
}

# Combine results into a single report
details := {"metric": [metric | metric := metrics_test[_]]}
