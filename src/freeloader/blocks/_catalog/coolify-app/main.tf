locals {
  api_base = endswith(var.coolify_endpoint, "/api/v1") ? var.coolify_endpoint : "${trimsuffix(var.coolify_endpoint, "/")}/api/v1"
  domains  = var.domain != "" ? "https://${var.domain}" : ""
}

# The Coolify terraform provider does not have a coolify_application resource.
# We use the API directly via local-exec to manage the full lifecycle.

provider "coolify" {
  endpoint = local.api_base
}

resource "terraform_data" "app" {
  input = {
    name                       = var.name
    server_uuid                = var.server_uuid
    project_uuid               = var.coolify_project_uuid
    environment_name           = var.environment_name
    destination_uuid           = var.destination_uuid
    docker_registry_image_name = var.registry_image_path
    docker_registry_image_tag  = var.docker_registry_image_tag
    ports_exposes              = var.ports_exposes
    domains                    = local.domains
    api_base                   = local.api_base
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      RESPONSE=$(curl -sf -X POST \
        -H "Authorization: Bearer $COOLIFY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
          "server_uuid": "${var.server_uuid}",
          "project_uuid": "${var.coolify_project_uuid}",
          "environment_name": "${var.environment_name}",
          "destination_uuid": "${var.destination_uuid}",
          "docker_registry_image_name": "${var.registry_image_path}",
          "docker_registry_image_tag": "${var.docker_registry_image_tag}",
          "ports_exposes": "${var.ports_exposes}",
          "name": "${var.name}",
          "domains": "${local.domains}",
          "instant_deploy": true
        }' \
        "${local.api_base}/applications/dockerimage")

      echo "$RESPONSE"
      APP_UUID=$(echo "$RESPONSE" | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
      echo "$APP_UUID" > ${path.module}/app_uuid.txt
      echo "Created application: $APP_UUID"
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      set -e
      if [ -f ${path.module}/app_uuid.txt ]; then
        APP_UUID=$(cat ${path.module}/app_uuid.txt)
        echo "Deleting application: $APP_UUID"
        curl -sf -X DELETE \
          -H "Authorization: Bearer $COOLIFY_TOKEN" \
          "${self.input.api_base}/applications/$APP_UUID" || true
        rm -f ${path.module}/app_uuid.txt
      fi
    EOT
  }
}

data "local_file" "app_uuid" {
  depends_on = [terraform_data.app]
  filename   = "${path.module}/app_uuid.txt"
}
