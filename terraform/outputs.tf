output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "public_ip" {
  description = "Public IP of the instance"
  value       = aws_instance.web.public_ip
}

output "public_dns" {
  description = "Public DNS of the instance"
  value       = aws_instance.web.public_dns
}

output "http_url" {
  description = "HTTP URL for the dashboard"
  value       = "http://${aws_instance.web.public_dns}"
}
