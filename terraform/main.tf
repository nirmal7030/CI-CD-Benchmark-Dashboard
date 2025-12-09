#############################################
# Networking: use default VPC + a public subnet
#############################################

# Fetch the default VPC
data "aws_vpc" "default" {
  default = true
}

# Fetch all subnets inside that default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for HTTP + optional SSH
resource "aws_security_group" "web_sg" {
  name        = "cicd-benchmark-web-sg-v2"
  description = "Allow HTTP from anywhere and SSH from my IP"
  vpc_id      = data.aws_vpc.default.id

  # HTTP 80 (for the container)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # OPTIONAL: SSH 22 (open for now, you can restrict later)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cicd-benchmark-web-sg-v2"
  }
}

#############################################
# IAM role so EC2 can talk to SSM
#############################################

resource "aws_iam_role" "ec2_role" {
  name = "cicd-benchmark-ec2-role-v2" # renamed to avoid duplication

  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
  EOF
}

resource "aws_iam_role_policy_attachment" "ec2_ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "cicd-benchmark-ec2-profile-v2" # renamed to match
  role = aws_iam_role.ec2_role.name
}

#############################################
# AMI: Amazon Linux 2023 (for Docker)
#############################################

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

#############################################
# EC2 instance
#############################################

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type

  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # If you want SSH access with a key pair, you can add:
  # key_name = "your-keypair-name"

  user_data = <<-EOF
  #!/bin/bash
  set -xe

  # Log to a file for debugging
  exec > /var/log/cicd-benchmark-user-data.log 2>&1

  # Update & install Docker + Git
  dnf update -y
  dnf install -y docker git

  systemctl enable docker
  systemctl start docker

  mkdir -p /opt
  cd /opt

  # Clone or update the repo
  if [ ! -d "cicd-benchmark" ]; then
    git clone https://github.com/${var.github_user}/${var.github_repo}.git cicd-benchmark
  else
    cd cicd-benchmark
    git pull
    cd ..
  fi

  cd cicd-benchmark

  # Build Docker image
  docker build -t cicd-benchmark:prod .

  # Stop previous container if it exists
  docker rm -f cicdbench || true

  # Run container on port 80 -> 8000
  docker run -d --name cicdbench -p 80:8000 \\
    -e SECRET_KEY="${var.secret_key}" \\
    -e BENCH_API_KEY="${var.bench_api_key}" \\
    -e DEBUG=0 \\
    cicd-benchmark:prod
  EOF

  tags = {
    Name = "cicd-benchmark-web-v2"
  }
}
