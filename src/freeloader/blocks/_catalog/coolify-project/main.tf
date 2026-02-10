locals {
  endpoint = endswith(var.coolify_endpoint, "/api/v1") ? var.coolify_endpoint : "${trimsuffix(var.coolify_endpoint, "/")}/api/v1"
}

provider "coolify" {
  endpoint = local.endpoint
}

resource "coolify_project" "project" {
  name        = var.name
  description = var.description != "" ? var.description : var.name
}
