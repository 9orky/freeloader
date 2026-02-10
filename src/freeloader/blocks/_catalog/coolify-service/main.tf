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
}

resource "coolify_service" "service" {
  name             = var.name
  server_uuid      = var.server_uuid
  project_uuid     = var.coolify_project_uuid
  destination_uuid = var.destination_uuid
  environment_name = var.environment_name
  instant_deploy   = false

  compose = local.compose
}

# The terraform provider does not support setting domains (urls) on services.
# We use the Coolify API directly to assign the FQDN and trigger deployment.
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

      # Set the domain on the 'app' service container
      if [ -n "${var.domain}" ]; then
        echo "Setting domain https://${var.domain} on service $SERVICE_UUID..."
        curl -sf -X PATCH \
          -H "Authorization: Bearer $COOLIFY_TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"urls": [{"name": "app", "url": "https://${var.domain}"}]}' \
          "$API/services/$SERVICE_UUID"
        echo ""
      fi

      # Start the service
      echo "Starting service $SERVICE_UUID..."
      curl -sf -X GET \
        -H "Authorization: Bearer $COOLIFY_TOKEN" \
        "$API/services/$SERVICE_UUID/start"
      echo ""
      echo "Service deployment triggered."
    EOT
  }
}
