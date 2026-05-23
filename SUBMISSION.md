# Submission — DevOps Engineer Assignment

- **Candidate name:** Anuj Kumar
- **Email:** gahlawatanuj5710@gmail.com
- **Date submitted:** 24-05-2026
- **Hours spent (approximate):** 10

## Deliverables checklist
- [x] Part A: Terraform code under /terraform applies cleanly on LocalStack
- [x] Part A: `terraform validate` and `terraform fmt -check` both pass
- [x] Part B: Janitor script runs in --dry-run mode and produces report.json
- [x] Part B: GitHub Actions workflow runs green on a fresh PR
- [x] Part B: --delete mode respects Protected=true tag
- [x] Part C: DESIGN.md is present and within 2 pages
- [ ] Walkthrough video link below is accessible (unlisted is fine)

## Walkthrough video
Link (Loom / YouTube unlisted / Google Drive):
Length: max 5 minutes

## Sample report
Path to a sample report.json produced by your script: `samples/report.example.json`
  
## Known limitations 
(bullet list — be honest)
* LocalStack v3.8 Community Edition APIs hang indefinitely on S3 lifecycle and versioning rules. I intentionally omitted these from the final `main.tf` to ensure automated CI/CD pipeline completion.
* The script currently uses sequential API calls (`boto3`). In an enterprise account with thousands of volumes, asynchronous calls (`aiobotocore`) would be required to prevent Lambda execution timeouts.
  
## AI usage disclosure
(see Section 7 of the brief)
* Tools Used: I used an LLM to generate the core Python boilerplate for `boto3`, structure the JSON schema, draft standard Terraform configurations, and outline the GitHub Actions CI/CD YAML.
* What it got wrong: 
    1. **Infrastructure:** The AI generated Terraform for S3 lifecycle and versioning rules that caused the LocalStack v3.8 API to hang indefinitely during the `apply` phase.
    2. **Version Control:** The AI generated PowerShell commands (`echo > .gitignore`) to set up file tracking, but it failed to account for Windows defaulting to UTF-16 encoding. Git requires UTF-8, so it ignored the file entirely and attempted to upload over 100MB of hidden `.terraform/` binaries.
    3. **CI/CD Configuration:** The AI generated a complex regex command for the LocalStack Docker `health-cmd` that failed to parse correctly within the GitHub Actions YAML runner, causing the container to be marked as unhealthy and killing the job.
* **Manual Code Section:** I manually stripped the unsupported S3 lifecycle blocks from `main.tf` to stabilize the deployment. I manually authored the `.gitignore` file to enforce UTF-8 encoding and purged the polluted Git history. Finally, I manually rewrote the Docker health check in the GitHub Actions workflow to use a standard HTTP 200 `curl` check. I chose to do these manually because LLMs often hallucinate support for specific local environments and overcomplicate shell commands inside YAML, and ensuring pipeline stability requires strict human oversight.