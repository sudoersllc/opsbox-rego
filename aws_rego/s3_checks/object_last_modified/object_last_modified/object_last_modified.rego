package aws_rego.s3_checks.object_last_modified.object_last_modified

import rego.v1

# Helper function to parse date strings
parse_date(date_string) := time.parse_rfc3339_ns(date_string)

# Calculate the difference in days between two timestamps
days_diff(start, end) := diff if {
	start_ns := parse_date(start)
	end_ns := parse_date(end)
	diff := ((end_ns - start_ns) / 1000000000) / 86400
}

# Check if the object is in STANDARD storage class and hasn't been modified in over 90 days
is_standard_and_old(s3object) if {
	"STANDARD" in object.StorageClass
}

# Count objects in STANDARD storage class and haven't been modified in over 90 days
count_standard_and_old := count([s3object | some s3object in input.objects[_]; is_standard_and_old(object)])

# Total number of objects
total_objects := count(input.objects)

# Calculate the percentage
percentage_standard_and_old := (100 * count_standard_and_old) / total_objects

allow if {
	percentage_standard_and_old >= 70
}

# Output details of the objects
standard_and_old_objects := [s3object | some s3object in input.objects[_]; is_standard_and_old(object)]

details := {
	"percentage_standard_and_old": percentage_standard_and_old,
	"standard_and_old_objects": standard_and_old_objects,
	"total_objects": total_objects,
}
