package aws_rego.s3_checks.object_last_modified.object_last_modified

import rego.v1

# Helper function to calculate the difference in days between two timestamps
days_diff(start, end) := diff if {
	diff := (end - start) / 86400 # Convert seconds to days
}

# Check if the object is in STANDARD storage class and hasn't been modified in over 90 days
is_standard_and_old(s3object) if {
	s3object.StorageClass == "STANDARD" # Ensure the storage class is STANDARD
	s3object.LastModified > 0 # Ensure LastModified is a valid timestamp
	now := time.now_ns() / 1000000000 # Current time in seconds
	days_diff(s3object.LastModified, now) > 90 # Check if the age is greater than 90 days
}

# Count objects in STANDARD storage class that haven't been modified in over 90 days
count_standard_and_old := count([s3object | some s3object in input.objects; is_standard_and_old(s3object)])

# Total number of objects
total_objects := count(input.objects)

# Calculate the percentage
percentage_standard_and_old := (100 * count_standard_and_old) / total_objects

# Allow rule based on percentage threshold
allow if {
	percentage_standard_and_old >= 70
}

# Output details of the objects
standard_and_old_objects := [s3object | some s3object in input.objects; is_standard_and_old(s3object)]

details := {
	"percentage_standard_and_old": percentage_standard_and_old,
	"standard_and_old_objects": standard_and_old_objects,
	"total_objects": total_objects,
}
