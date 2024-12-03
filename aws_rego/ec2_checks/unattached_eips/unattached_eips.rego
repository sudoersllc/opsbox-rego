package aws.cost.unattached_eips

default allow = false

allow {
    eip := input.eips[_]
    eip.association_id == "" # Check if association_id is empty
}

details := [eip | eip := input.eips[_]; eip.association_id == ""]