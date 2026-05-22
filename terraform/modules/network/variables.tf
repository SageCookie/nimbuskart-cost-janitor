variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
  default     = "staging"
}

variable "project" {
  description = "Project name for tagging"
  type        = string
  default     = "nimbuskart"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "devops-team"
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH into instances"
  type        = string
  default     = "0.0.0.0/0"
}