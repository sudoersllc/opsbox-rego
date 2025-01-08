package aws_rego.elb_checks.inactive_load_balancers.inactive_load_balancers

import rego.v1

# Rule to identify inactive ELBs based on instance health

allow if {
	elb | 
		some elb in input.elbs;                       
		some instance in elb.InstanceHealth;          
		instance.State == "unhealthy"   
}
details := [elb | 
    some elb in input.elbs;                       
    some instance in elb.InstanceHealth;          
    instance.State == "unhealthy"                   
]