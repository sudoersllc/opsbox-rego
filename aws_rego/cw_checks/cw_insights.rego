package aws.get_metrics
metrics_test[metric] {
    metric := input.metrics[_]
}

# Combine results into a single report
details := {
    "metric": [ metric| metric := metrics_test[_]],
}