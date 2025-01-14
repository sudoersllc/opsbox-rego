package aws_rego.ec2_checks.unattached_eips.unattached_eips

import rego.v1

allow if {
eip |
	some eip in input.eips
	eip.association_id == "" # Check if association_id is empty
}

details := [eip | some eip in input.eips; eip.association_id == ""]
