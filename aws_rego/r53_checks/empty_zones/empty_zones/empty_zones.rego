package aws.cost.empty_zones

empty_hosted_zones[zone] {
    zone := input.hosted_zones[_]
}

any_records_in_zone(zone_id) {
    record := input.records[_]
    record.zone_id == zone_id
}

details := {
    "empty_hosted_zones": [zone | zone := empty_hosted_zones[_]],
}
