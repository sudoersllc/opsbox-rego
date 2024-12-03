package aws.cost.object_last_modified

import future.keywords.in

# Helper function to parse date strings
parse_date(date_string) = parsed_date {
    parsed_date := time.parse_rfc3339_ns(date_string)
}

# Calculate the difference in days between two timestamps
days_diff(start, end) = diff {
    start_ns := parse_date(start)
    end_ns := parse_date(end)
    diff := (end_ns - start_ns) / 1000000000 / 86400
}

# Check if the object is in STANDARD storage class and hasn't been modified in over 90 days
is_standard_and_old(object) {
    object.StorageClass == "STANDARD"
}

# Count objects in STANDARD storage class and haven't been modified in over 90 days
count_standard_and_old := count([object | object := input.objects[_]; is_standard_and_old(object)])

# Total number of objects
total_objects := count(input.objects)

# Calculate the percentage
percentage_standard_and_old := 100 * count_standard_and_old / total_objects

# Define the policy to check if 70% or more objects are in STANDARD storage class and haven't been modified in over 90 days
allow {
    percentage_standard_and_old >= 70
}

# Output details of the objects
standard_and_old_objects := [object | object := input.objects[_]; is_standard_and_old(object)]

details := {
    "percentage_standard_and_old": percentage_standard_and_old,
    "standard_and_old_objects": standard_and_old_objects,
    "total_objects": total_objects
}