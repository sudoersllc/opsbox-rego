# OpsBox Rego Checks for AWS ELB

This package contains various Rego check plugins related to AWS's Elastic Load Balancing (ELB) service, including:

- **Low Request Count Load Balancers (`low_request_counts`)**
- **High Error Rate Load Balancers (`high_error_rate`)**
- **Inactive Load Balancers (`inactive_load_balancers`)**

---

## Plugin Descriptions

### Low Request Count Load Balancers (`low_request_counts`)
Identifies load balancers with low request counts, providing performance insights and opportunities to optimize or decommission underutilized resources.

### High Error Rate Load Balancers (`high_error_rate`)
Detects load balancers with high error rates, helping identify and address performance issues or misconfigurations to improve application reliability.

### Inactive Load Balancers (`inactive_load_balancers`)
Finds load balancers that are inactive, offering recommendations to decommission these resources to reduce unnecessary costs.