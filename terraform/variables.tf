variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "github_user" {
  description = "GitHub username for repository clone"
  type        = string
}

variable "github_repo" {
  description = "GitHub repo name containing the Django project"
  type        = string
}

variable "secret_key" {
  description = "Django SECRET_KEY for app environment"
  type        = string
  sensitive   = true
}

variable "bench_api_key" {
  description = "API key for metric ingestion"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}
