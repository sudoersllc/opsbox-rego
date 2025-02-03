# OpsBox Rego Checks for AWS Route 53

This module contains a Rego check plugin related to AWS's Route 53 service:

- **Empty Route 53 Hosted Zones (`empty_zones`)**

---

## Plugin Description

### Empty Route 53 Hosted Zones Plugin (`empty_zones`)
Identifies Route 53 hosted zones with no DNS records to optimize DNS management by pinpointing zones that can be deleted or reviewed.

---