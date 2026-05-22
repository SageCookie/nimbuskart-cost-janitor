output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.network.vpc_id
}

output "subnet_ids" {
  description = "The IDs of the public subnets"
  value       = [module.network.public_subnet_1_id, module.network.public_subnet_2_id]
}

output "log_bucket_name" {
  description = "The name of the S3 bucket for application logs"
  value       = aws_s3_bucket.app_logs.id
}