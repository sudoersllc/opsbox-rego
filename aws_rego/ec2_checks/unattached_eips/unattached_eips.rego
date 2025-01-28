package aws_rego.ec2_checks.unattached_eips.unattached_eips

import rego.v1


details := [eip | some eip in input.eips; eip.association_id == ""]
