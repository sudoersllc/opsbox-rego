package aws_rego.r53_checks.empty_zones.empty_zones

import rego.v1

empty_hosted_zones contains zone if {
zone |
	some zone in input.hosted_zones[_]
}

any_records_in_zone(zone_id) if {
record |
	some record in input.records[_]
	record.zone_id == zone_id
}

details := {"empty_hosted_zones": [zone | zone := empty_hosted_zones[_]]}
