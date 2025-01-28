package aws_rego.s3_checks.object_last_modified.object_last_modified

import rego.v1

# Check if the object is in STANDARD storage class and hasn't been modified before the threshold date
is_standard_and_old(s3object) if {
	s3object.StorageClass == "STANDARD" # Ensure the storage class is STANDARD
	s3object.LastModified > 0 # Ensure LastModified is a valid timestamp
	s3object.LastModified < input.s3_last_modified_date_threshold # Check if the age is greater than the threshold
}

# Count objects in STANDARD storage class that haven't been modified before the threshold date
count_standard_and_old := count([s3object | some s3object in input.objects; is_standard_and_old(s3object)])

# Total number of objects
total_objects := count(input.objects)

# Calculate the percentage
percentage_standard_and_old := (100 * count_standard_and_old) / total_objects

# Allow rule based on percentage threshold

# Output details of the objects
standard_and_old_objects := [s3object | some s3object in input.objects; is_standard_and_old(s3object)]

details := {
	"percentage_standard_and_old": percentage_standard_and_old,
	"standard_and_old_objects": standard_and_old_objects,
	"total_objects": total_objects,
}
