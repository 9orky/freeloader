output "app_uuid" {
  value = trimspace(data.local_file.app_uuid.content)
}

output "app_url" {
  value = var.domain != "" ? "https://${var.domain}" : "http://${var.name}.localhost"
}
