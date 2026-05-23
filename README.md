# NimbusKart Cost Janitor

## Overview
The NimbusKart Cost Janitor is a multi-cloud cost hygiene and automation tool designed to detect and safely eliminate wasted cloud spend. This repository provisions a baseline simulated AWS infrastructure using Terraform and LocalStack, and deploys a Python-based automation engine to hunt down unattached EBS volumes, long-stopped EC2 instances, unassociated Elastic IPs, and untagged resources. The entire workflow is hardened with a strict CI/CD pipeline via GitHub Actions that automatically runs detections and prevents wasteful infrastructure from merging into production.

## How to run locally
Ensure you have Docker, Terraform (v1.5+), and Python 3.10+ installed.

```bash
# 1. Clone the repository
git clone [https://github.com/SageCookie/nimbuskart-cost-janitor.git]
(https://github.com/SageCookie/nimbuskart-cost-janitor.git)
cd nimbuskart-cost-janitor

# 2. Boot the simulated AWS environment (LocalStack)
docker run --rm -dp 4566:4566 --name localstack localstack/localstack:3.8

# 3. Provision the infrastructure
cd terraform
$env:AWS_ENDPOINT_URL="http://localhost:4566"  # Windows (Use export for Linux/Mac)
terraform init
terraform apply -auto-approve

# 4. Run the Cost Janitor
cd ../janitor
python -m venv venv
.\venv\Scripts\Activate  # Windows (Use source venv/bin/activate for Linux/Mac)
pip install -r requirements.txt
python janitor.py --dry-run

## Decisions & deviations
Pinned LocalStack to v3.8: I explicitly avoided the latest tag because LocalStack recently introduced a mandatory authentication token wall for their community image. Pinning to 3.8 ensures true zero-cost, zero-auth local execution.

Omitted S3 Lifecycle/Versioning rules: LocalStack v3.8 Community Edition APIs hang indefinitely when attempting to process advanced S3 lifecycle configurations. I intentionally stripped these from the final main.tf to ensure automated CI/CD pipeline completion.

Bypassed tflocal wrapper: I routed standard Terraform natively using the AWS_ENDPOINT_URL environment variable rather than relying on the terraform-local python wrapper, eliminating Windows path resolution issues and reducing unnecessary dependencies.

Unsafe SSH Default Flagged: The spec requested opening port 22 to 0.0.0.0/0. I implemented this as requested to satisfy the network baseline but heavily strongly advise restricting this CIDR block to a Bastion host or VPN subnet in production.

Trade-offs
If I had one more week to work on this, I would implement an asynchronous Boto3 strategy (using aiobotocore) within the Python script. The current synchronous looping mechanism is highly effective for a staging environment, but in an enterprise AWS account with tens of thousands of volumes, synchronous calls risk hitting Lambda execution timeouts. Furthermore, I would migrate Terraform's state management from local .tfstate files to a remote backend (S3 + DynamoDB locking) to secure team collaboration.