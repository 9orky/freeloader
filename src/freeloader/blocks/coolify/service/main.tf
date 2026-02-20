terraform {
  required_providers {
    coolify = {
      source  = "sierrajc/coolify"
      version = "~> 0.10"
    }
  }
}

variable "name" {
  type = string
}

variable "coolify_token" {
  type      = string
  sensitive = true
}

variable "server_uuid" {
  type = string
}

variable "coolify_endpoint" {
  type = string
}

variable "platform_project_uuid" {
  type = string
}

variable "destination_uuid" {
  type = string
}

variable "environment_name" {
  type    = string
  default = "production"
}

variable "compose" {
  type    = string
  default = ""
}

variable "registry_image_path" {
  type    = string
  default = ""
}

variable "domain" {
  type    = string
  default = ""
}

locals {
  endpoint = endswith(var.coolify_endpoint, "/api/v1") ? var.coolify_endpoint : "${trimsuffix(var.coolify_endpoint, "/")}/api/v1"

  default_compose = <<-EOF
services:
  app:
    image: "${var.registry_image_path}:latest"
    environment:
      - SERVICE_FQDN_APP
EOF

  compose = var.compose != "" ? var.compose : local.default_compose
}

provider "coolify" {
  endpoint = local.endpoint
  token    = var.coolify_token
}

resource "coolify_service" "service" {
  name             = var.name
  server_uuid      = var.server_uuid
  project_uuid     = var.platform_project_uuid
  destination_uuid = var.destination_uuid
  environment_name = var.environment_name
  instant_deploy   = false

  compose = local.compose
}

resource "terraform_data" "configure_and_deploy" {
  depends_on = [coolify_service.service]

  triggers_replace = [
    coolify_service.service.uuid,
    var.domain,
    local.compose,
  ]

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      SERVICE_UUID="${coolify_service.service.uuid}"
      API="${local.endpoint}"

      if [ -n "${var.domain}" ]; then
        echo "Setting domain https://${var.domain} on service $SERVICE_UUID..."
        curl -sf -X PATCH \
          -H "Authorization: Bearer ${var.coolify_token}" \
          -H "Content-Type: application/json" \
          -d '{"urls": [{"name": "app", "url": "https://${var.domain}"}]}' \
          "$API/services/$SERVICE_UUID"
        echo ""
      fi

      echo "Starting service $SERVICE_UUID..."
      curl -sf -X GET \
        -H "Authorization: Bearer ${var.coolify_token}" \
        "$API/services/$SERVICE_UUID/start"
      echo ""
      echo "Service deployment triggered."
    EOT
  }
}

output "service_uuid" {
  value = coolify_service.service.uuid
}

output "app_url" {
  value = var.domain != "" ? "https://${var.domain}" : "http://${var.name}.localhost"
}
