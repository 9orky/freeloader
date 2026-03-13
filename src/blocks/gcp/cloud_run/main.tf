terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

variable "gcp_service_account_json" {
  type      = string
  sensitive = true
}

variable "name" {
  type = string
}

variable "project_id" {
  type    = string
  default = ""
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "registry_image_path" {
  type = string
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "max_instances" {
  type    = number
  default = 1
}

variable "allow_unauthenticated" {
  type    = bool
  default = true
}

variable "env_json" {
  type    = string
  default = "{}"
}

locals {
  service_account = jsondecode(var.gcp_service_account_json)
  name_parts      = regexall("[a-z0-9]+", lower(var.name))
  trimmed_name    = length(local.name_parts) > 0 ? join("-", local.name_parts) : ""
  service_name    = trimsuffix(substr("app-${local.trimmed_name != "" ? local.trimmed_name : "service"}", 0, 63), "-")
  project_id      = trimspace(var.project_id) != "" ? trimspace(var.project_id) : local.service_account.project_id
  image_ref       = "${var.registry_image_path}:${var.image_tag}"
  env_map         = tomap(try(jsondecode(var.env_json), {}))
}

provider "google" {
  credentials = var.gcp_service_account_json
  project     = local.project_id
  region      = var.region
}

resource "google_cloud_run_v2_service" "app" {
  name                 = local.service_name
  location             = var.region
  project              = local.project_id
  deletion_protection  = false
  ingress              = "INGRESS_TRAFFIC_ALL"
  invoker_iam_disabled = var.allow_unauthenticated

  scaling {
    max_instance_count = var.max_instances
  }

  template {
    containers {
      image = local.image_ref

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle = true
      }

      dynamic "env" {
        for_each = local.env_map
        content {
          name  = env.key
          value = tostring(env.value)
        }
      }
    }
  }
}

output "app_url" {
  value = google_cloud_run_v2_service.app.uri
}

output "app_id" {
  value = google_cloud_run_v2_service.app.name
}