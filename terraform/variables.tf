variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
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