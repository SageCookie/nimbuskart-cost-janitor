import argparse
import boto3
import json
import os
import sys
from datetime import datetime, timezone
from constants import EBS_GP3_GB_MONTH_USD, ELASTIC_IP_MONTH_USD, EC2_T3_MICRO_MONTH_USD

REQUIRED_TAGS = {"Project", "Environment", "Owner"}

class CostJanitor:
    def __init__(self, region="us-east-1", endpoint_url=None, stop_days=14):
        self.region = region
        self.stop_days = stop_days
        # If AWS_ENDPOINT_URL is set in the environment, use it (crucial for LocalStack)
        self.endpoint_url = endpoint_url or os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
        
        # Initialize Boto3 EC2 client with mock credentials for local testing
        self.ec2 = boto3.client(
            'ec2', 
            region_name=self.region, 
            endpoint_url=self.endpoint_url,
            aws_access_key_id="mock_key",
            aws_secret_access_key="mock_secret"
        )
        self.now = datetime.now(timezone.utc)
        self.findings = []

    def _parse_tags(self, tags_list):
        """Helper to convert AWS tag lists into a flat dictionary."""
        if not tags_list:
            return {}
        return {tag['Key']: tag['Value'] for tag in tags_list}

    def _check_missing_tags(self, tags_dict):
        """Returns True if any required tag is missing."""
        return not REQUIRED_TAGS.issubset(tags_dict.keys())

    def scan_ebs_volumes(self):
        """Finds unattached EBS volumes and volumes missing required tags."""
        response = self.ec2.describe_volumes()
        for vol in response.get('Volumes', []):
            vol_id = vol['VolumeId']
            tags = self._parse_tags(vol.get('Tags', []))
            is_protected = tags.get('Protected', '').lower() == 'true'
            
            # Pattern 1: Unattached volume
            if not vol['Attachments']:
                size_gb = vol['Size']
                cost = size_gb * EBS_GP3_GB_MONTH_USD
                self.findings.append({
                    "resource_id": vol_id,
                    "resource_type": "ebs_volume",
                    "reason": "unattached",
                    "age_days": (self.now - vol['CreateTime']).days,
                    "estimated_monthly_cost_usd": round(cost, 2),
                    "tags": tags if tags else {"Project": None, "Environment": None},
                    "suggested_action": "delete",
                    "safe_to_auto_delete": not is_protected
                })
            # Pattern 4: Missing tags
            elif self._check_missing_tags(tags):
                self.findings.append({
                    "resource_id": vol_id,
                    "resource_type": "ebs_volume",
                    "reason": "missing_required_tags",
                    "age_days": (self.now - vol['CreateTime']).days,
                    "estimated_monthly_cost_usd": 0.00,
                    "tags": tags if tags else {"Project": None, "Environment": None},
                    "suggested_action": "tag",
                    "safe_to_auto_delete": False
                })

    def scan_ec2_instances(self):
        """Finds instances stopped for > N days and instances missing required tags."""
        response = self.ec2.describe_instances()
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                inst_id = instance['InstanceId']
                tags = self._parse_tags(instance.get('Tags', []))
                is_protected = tags.get('Protected', '').lower() == 'true'
                
                # AWS doesn't expose strict stop time easily, so we use LaunchTime as a fallback approximation 
                # in a real scenario we'd use CloudTrail or StateTransitionReason.
                age_days = (self.now - instance['LaunchTime']).days

                # Pattern 2: Stopped instances
                if instance['State']['Name'] == 'stopped' and age_days >= self.stop_days:
                    self.findings.append({
                        "resource_id": inst_id,
                        "resource_type": "ec2_instance",
                        "reason": f"stopped_>_{self.stop_days}_days",
                        "age_days": age_days,
                        "estimated_monthly_cost_usd": EC2_T3_MICRO_MONTH_USD,
                        "tags": tags if tags else {"Project": None, "Environment": None},
                        "suggested_action": "delete",
                        "safe_to_auto_delete": not is_protected
                    })
                # Pattern 4: Missing tags
                elif self._check_missing_tags(tags):
                    self.findings.append({
                        "resource_id": inst_id,
                        "resource_type": "ec2_instance",
                        "reason": "missing_required_tags",
                        "age_days": age_days,
                        "estimated_monthly_cost_usd": 0.00,
                        "tags": tags if tags else {"Project": None, "Environment": None},
                        "suggested_action": "tag",
                        "safe_to_auto_delete": False
                    })

    def scan_elastic_ips(self):
        """Finds unassociated Elastic IPs."""
        response = self.ec2.describe_addresses()
        for eip in response.get('Addresses', []):
            eip_id = eip.get('AllocationId', eip.get('PublicIp'))
            tags = self._parse_tags(eip.get('Tags', []))
            is_protected = tags.get('Protected', '').lower() == 'true'

            # Pattern 3: Unassociated EIP
            if 'InstanceId' not in eip and 'NetworkInterfaceId' not in eip:
                self.findings.append({
                    "resource_id": eip_id,
                    "resource_type": "elastic_ip",
                    "reason": "unassociated",
                    "age_days": 0, # EIPs don't have creation dates in standard describe API
                    "estimated_monthly_cost_usd": ELASTIC_IP_MONTH_USD,
                    "tags": tags if tags else {"Project": None, "Environment": None},
                    "suggested_action": "release",
                    "safe_to_auto_delete": not is_protected
                })

    def execute_deletions(self):
        """Attempts to delete resources marked as safe_to_auto_delete."""
        print("\n--- Executing Deletions ---")
        for finding in self.findings:
            if finding['safe_to_auto_delete'] and finding['suggested_action'] in ['delete', 'release']:
                res_id = finding['resource_id']
                res_type = finding['resource_type']
                try:
                    if res_type == "ebs_volume":
                        self.ec2.delete_volume(VolumeId=res_id)
                        print(f"[DELETED] Volume: {res_id}")
                    elif res_type == "ec2_instance":
                        self.ec2.terminate_instances(InstanceIds=[res_id])
                        print(f"[TERMINATED] Instance: {res_id}")
                    elif res_type == "elastic_ip":
                        self.ec2.release_address(AllocationId=res_id)
                        print(f"[RELEASED] Elastic IP: {res_id}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete {res_id}: {str(e)}")

    def generate_reports(self):
        """Generates the required report.json and a Markdown summary."""
        total_waste = sum(f['estimated_monthly_cost_usd'] for f in self.findings)
        
        # Exact schema required by Part B
        report_data = {
            "scan_timestamp": self.now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "account_id": "000000000000", # Mock account ID for LocalStack
            "region": self.region,
            "summary": {
                "total_orphans": len(self.findings),
                "estimated_monthly_waste_usd": round(total_waste, 2)
            },
            "findings": self.findings
        }

        # Write JSON
        with open("report.json", "w") as f:
            json.dump(report_data, f, indent=4)
        print("Generated report.json")

        # Write Markdown
        md_content = f"# Cost Janitor Scan Summary\n\n"
        md_content += f"**Scan Time:** {report_data['scan_timestamp']}\n"
        md_content += f"**Total Orphans Found:** {report_data['summary']['total_orphans']}\n"
        md_content += f"**Estimated Monthly Waste:** ${report_data['summary']['estimated_monthly_waste_usd']}\n\n"
        md_content += "### Findings\n"
        for finding in self.findings:
            md_content += f"- **{finding['resource_id']}** ({finding['resource_type']}): {finding['reason']} (${finding['estimated_monthly_cost_usd']}/mo)\n"

        with open("report.md", "w") as f:
            f.write(md_content)
        print("Generated report.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NimbusKart Multi-Cloud Cost Janitor")
    parser.add_argument('--delete', action='store_true', help="Execute deletion of safe orphans")
    parser.add_argument('--dry-run', action='store_true', default=True, help="Run without deleting (default)")
    parser.add_argument('--days', type=int, default=14, help="Days threshold for stopped instances")
    args = parser.parse_args()

    # If --delete is passed, it overrides --dry-run
    is_dry_run = not args.delete

    janitor = CostJanitor(stop_days=args.days)
    janitor.scan_ebs_volumes()
    janitor.scan_ec2_instances()
    janitor.scan_elastic_ips()
    
    janitor.generate_reports()

    if not is_dry_run:
        janitor.execute_deletions()
    
    # Requirement: Non-zero exit code if orphans found in dry-run mode
    if is_dry_run and len(janitor.findings) > 0:
        print("\n[ALERT] Orphans found during dry-run. Exiting with code 1 to fail CI pipeline.")
        sys.exit(1)