variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
}

variable "github_user" {
  description = "GitHub username / org that hosts the repo"
  type        = string
}

variable "github_repo" {
  description = "Repository name containing the cicd-benchmark app"
  type        = string
}

variable "secret_key" {
  description = "Django SECRET_KEY to use on the server"
  type        = string
  sensitive   = true
}

variable "bench_api_key" {
  description = "Shared API key for /api/metrics/ingest"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "EC2 instance type for the web server"
  type        = string
  default     = "t3.small"
}
