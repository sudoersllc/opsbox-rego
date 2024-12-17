package aws.cost.stray_ebs

default allow = false

allow {
    volume := input.volumes[_]
    not volume.state == "in-use"
}

details := [volume | volume := input.volumes[_]; not volume.state == "in-use"]