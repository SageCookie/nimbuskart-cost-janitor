"""
Pricing Constants for NimbusKart Cost Janitor.
Source: AWS Pricing Calculator (us-east-1) - https://calculator.aws/
Assumption: 1 month = 730 hours.
"""

# EBS gp3 storage: $0.08 per GB-month
EBS_GP3_GB_MONTH_USD = 0.08

# Idle Elastic IP: $0.005 per hour -> ~$3.65 per month
ELASTIC_IP_MONTH_USD = 3.65

# t3.micro Linux instance (stopped instances don't incur compute charges, 
# but their attached EBS volumes do. We will use a flat estimate for the 
# compute capacity waste if it were left running/reserved).
# $0.0104 per hour -> ~$7.59 per month
EC2_T3_MICRO_MONTH_USD = 7.59