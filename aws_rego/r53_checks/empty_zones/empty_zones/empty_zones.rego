package aws_rego.r53_checks.empty_zones.empty_zones

import rego.v1

# Find hosted zones with no records
empty_hosted_zones contains zone if {
	some zone in input.hosted_zones
	not records_exist_for_zone(zone.id)
}

# Check if records exist for a given zone
records_exist_for_zone(zone_id) if {
	some record in input.records
	record.zone_id == zone_id
}

allow if {
	some zone in input.hosted_zones
	not records_exist_for_zone(zone.id)
}

# Generate details for empty hosted zones
details := {"empty_hosted_zones": [zone | zone := empty_hosted_zones[_]]}
