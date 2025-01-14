package aws_rego.rds_checks.scaling_down.scaling_down

import rego.v1

default allow := false

# Combine recommendations into a single report
details := {"recommendations_for_scaling_down": [
recommendation |
	some recommendation in input.rds_instances
	recommendation.CPUUtilization < 20
]}
