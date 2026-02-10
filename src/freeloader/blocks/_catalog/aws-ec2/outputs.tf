output "ip_address" {
  value = aws_instance.server.public_ip
}

output "instance_id" {
  value = aws_instance.server.id
}

output "ssh_user" {
  value = "ubuntu"
}

output "public_dns" {
  value = aws_instance.server.public_dns
}
