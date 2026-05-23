# NimbusKart Cost Janitor: System Design & Scaling Note

## 1. Multi-Cloud Reality (Scaling to GCP/Azure)
If we need to add GCP next quarter, we shouldn't have to rewrite the whole script. I would restructure this using a standard "Provider" approach. The main brain of the script (`janitor/core/`) would just say "find orphans and delete them," without caring what cloud they live in.

Then, I'd build separate translator files (like `providers/aws.py` and `providers/gcp.py`). The GCP file's only job would be to fetch GCP disks and translate them into a standard `OrphanResource` format that our main script already understands.

## 2. Minimal IAM Permissions
Running a script that deletes things is scary, so we have to keep the permissions incredibly tight.

**For Read-Only Mode (`--dry-run`):**
The script only needs to look around. Zero write access. The exact minimal policy is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeInstances",
        "ec2:DescribeAddresses"
      ],
      "Resource": "*"
    }
  ]
}
```

**For Active Mode (`--delete`):**
We would add the delete permissions (ec2:DeleteVolume, etc.), but I would strictly tie them to an IAM condition checking for the Protected tag. That way, even if the Python code glitches, AWS itself will block the deletion of protected resources.

## 3. The Safety Net: Real-World Failure Modes
Blindly deleting infrastructure usually leads to an outage eventually. Here are two ways this could blow up and how I'd prevent them:

**Failure Mode 1: The "We Just Built That" Problem.** Sometimes engineers spin up a massive cluster, but their script to apply tags fails or runs a few minutes late. Our Janitor might see an "untagged" database and instantly delete it.

**The Fix:** A hardcoded Minimum Age limit. The script should completely ignore any resource that is less than 48 hours old, giving people time to finish their setups.

**Failure Mode 2: The Logic Bug.** A bad code update or an AWS API change could confuse the script into thinking everything in the account is an orphan.

**The Fix:** A Circuit Breaker. If the script tries to delete more than 20 items (or $500 worth of stuff) in a single run, it should panic, abort the deletion entirely, and page the DevOps team to look at it manually.

## 4. Observability for FinOps
We need to know if this tool is actually working or if it broke silently. I would send these three metrics to our monitoring dashboard (like Datadog or CloudWatch):

- **Metric:** `janitor_pipeline_health`

  **Why:** To trigger an alert if the GitHub Action fails to run for more than 30 hours. A dead cron job doesn't clean up anything.

- **Metric:** `total_orphans_found`

  **Why:** To alert the DevOps team if this suddenly spikes to a high number (like 50+). If there are suddenly tons of orphans, it means our main infrastructure teardown process is broken somewhere else.

- **Metric:** `estimated_waste_prevented_usd`

  **Why:** No alerts for this one; it just sits on a dashboard so the FinOps team can clearly see how much money this script is saving the company every month.

## 5. What I did not build
Because this is a local proof-of-concept, I left Terraform's state files local (.tfstate). In a real team environment, doing that is a massive security risk and guarantees merge conflicts, so I would absolutely move the state to an S3 bucket with DynamoDB locking.

I also kept the Python script simple by using standard, synchronous API calls. This is perfectly fine for a small test environment, but if we ran this in a massive enterprise AWS account with 10,000 volumes, it would probably hit a timeout limit. In that case, I'd rewrite the boto3 calls to be asynchronous using aiobotocore.
