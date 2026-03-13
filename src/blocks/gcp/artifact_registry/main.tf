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

variable "location" {
  type    = string
  default = "us-central1"
}

variable "project_id" {
  type    = string
  default = ""
}

variable "repository_id" {
  type    = string
  default = ""
}

variable "image_name" {
  type    = string
  default = ""
}

locals {
  service_account = jsondecode(var.gcp_service_account_json)
  name_parts      = regexall("[a-z0-9]+", lower(var.name))
  trimmed_name    = length(local.name_parts) > 0 ? join("-", local.name_parts) : ""
  project_id      = trimspace(var.project_id) != "" ? trimspace(var.project_id) : local.service_account.project_id
  repository_id   = trimspace(var.repository_id) != "" ? trimspace(var.repository_id) : trimsuffix(substr("repo-${local.trimmed_name != "" ? local.trimmed_name : "app"}", 0, 63), "-")
  image_name      = trimspace(var.image_name) != "" ? trimspace(var.image_name) : (local.trimmed_name != "" ? local.trimmed_name : "app")
}

provider "google" {
  credentials = var.gcp_service_account_json
  project     = local.project_id
}

resource "google_artifact_registry_repository" "registry" {
  location      = var.location
  project       = local.project_id
  repository_id = local.repository_id
  description   = "Managed by freeloader"
  format        = "DOCKER"
}

output "host" {
  value = "${var.location}-docker.pkg.dev"
}

output "user" {
  value = "_json_key"
}

output "token" {
  value     = var.gcp_service_account_json
  sensitive = true
}

output "image_path" {
  value = "${google_artifact_registry_repository.registry.registry_uri}/${local.image_name}"
}

output "project_id" {
  value = nonsensitive(local.project_id)
}

output "repository_id" {
  value = google_artifact_registry_repository.registry.repository_id
}