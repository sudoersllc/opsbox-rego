package aws.cost.stray_instances

import future.keywords.in
import future.keywords.if

# Define business hours (9 AM to 5 PM)
business_hours := {"start": 9, "end": 17}

# Helper function to parse the launch time and extract the hour
launch_hour(launch_time) = hour {
    # Assume launch_time is in the format "2023-07-15T14:00:00Z"
    split_time := split(launch_time, "T")
    time_part := split_time[1]
    hour_part := split(time_part, ":")[0]
    hour := to_number(hour_part)
}

# Helper function to determine if a given hour is within business hours
time_within_business_hours(hour) {
    hour >= business_hours.start
    hour < business_hours.end
}

# Rule to identify instances running out-of-hours
out_of_hours_instances[instance] {
    instance := input.instances[_]
    instance.state == "running"
    hour := launch_hour(instance.launch_time)
    not time_within_business_hours(hour)
}

# Entry point for OPA to evaluate
default allow = false

details := [instance | instance := out_of_hours_instances]
