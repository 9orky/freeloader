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

variable "description" {
  type    = string
  default = ""
}

variable "coolify_endpoint" {
  type = string
}

locals {
  endpoint = endswith(var.coolify_endpoint, "/api/v1") ? var.coolify_endpoint : "${trimsuffix(var.coolify_endpoint, "/")}/api/v1"
}

provider "coolify" {
  endpoint = local.endpoint
  token    = var.coolify_token
}

resource "coolify_project" "project" {
  name        = var.name
  description = var.description != "" ? var.description : var.name
}

output "project_uuid" {
  value = coolify_project.project.uuid
}

output "project_name" {
  value = coolify_project.project.name
}
