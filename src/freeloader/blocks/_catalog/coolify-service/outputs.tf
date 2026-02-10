output "service_uuid" {
  value = coolify_service.service.uuid
}

output "app_url" {
  value = var.domain != "" ? "https://${var.domain}" : "http://${var.name}.localhost"
}
