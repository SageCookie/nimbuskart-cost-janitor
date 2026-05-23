terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# The provider block is set to mock credentials for LocalStack
provider "aws" {
  region                      = var.region
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
}

# Calling the network module we built
module "network" {
  source      = "./modules/network"
  project     = var.project
  environment = var.environment
  owner       = var.owner
}

# Two t3.micro EC2 instances tagged as web tier
resource "aws_instance" "web" {
  count                       = 2
  ami                         = "ami-0c55b159cbfafe1f0" # Mock Amazon Linux 2 AMI
  instance_type               = "t3.micro"
  subnet_id                   = count.index == 0 ? module.network.public_subnet_1_id : module.network.public_subnet_2_id
  vpc_security_group_ids      = [module.network.web_sg_id]
  associate_public_ip_address = true

  tags = {
    Name        = "${var.project}-web-${count.index + 1}"
    Tier        = "web"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

# S3 bucket for logs
resource "aws_s3_bucket" "app_logs" {
  bucket = "${var.project}-app-logs-${var.environment}-001"

  tags = {
    Name        = "${var.project}-app-logs"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}
/*
# Enable versioning for the S3 bucket
resource "aws_s3_bucket_versioning" "app_logs_versioning" {
  bucket = aws_s3_bucket.app_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rule to expire non-current versions after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "app_logs_lifecycle" {
  bucket = aws_s3_bucket.app_logs.id

  rule {
    filter{}
    id     = "expire-non-current"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
*/
# One intentionally unattached EBS volume (Our "orphan")
resource "aws_ebs_volume" "orphan_volume" {
  availability_zone = "us-east-1a"
  size              = 10

  tags = {
    Name        = "${var.project}-orphan-vol"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}