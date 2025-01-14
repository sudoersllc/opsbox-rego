package aws_rego.ec2_checks.stray_ebs.stray_ebs

import rego.v1

allow if {
volume |
	some volume in input.volumes
	not volume.state == "in-use"
}

details := [volume | some volume in input.volumes; not volume.state == "in-use"]
