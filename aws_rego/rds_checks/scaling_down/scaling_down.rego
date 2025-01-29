package aws_rego.rds_checks.scaling_down.scaling_down

import rego.v1


# Combine recommendations into a single report
details := {"recommendations_for_scaling_down": [
recommendation |
	some recommendation in input.rds_instances
	recommendation.CPUUtilization < input.rds_cpu_scaling_threshold
]}
