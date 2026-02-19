terraform {
  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 3.0"
    }
  }
}

variable "name" {
  type = string
}

variable "gitlab_token" {
  type      = string
  sensitive = true
}

variable "description" {
  type    = string
  default = ""
}

variable "visibility" {
  type    = string
  default = "private"
}

variable "token_scopes" {
  type    = list(string)
  default = ["read_registry", "write_registry"]
}

provider "gitlab" {
  token = var.gitlab_token
}

resource "gitlab_project" "project" {
  name                           = var.name
  path                           = var.name
  visibility_level               = var.visibility
  description                    = var.description
  initialize_with_readme         = true
  container_registry_access_level = "private"
}

resource "gitlab_project_access_token" "registry_token" {
  project    = gitlab_project.project.id
  name       = "freeloader-${var.name}"
  scopes     = var.token_scopes
  expires_at = formatdate("YYYY-MM-DD", timeadd(timestamp(), "8760h"))
}

output "host" {
  value = "registry.gitlab.com"
}

output "token" {
  value     = gitlab_project_access_token.registry_token.token
  sensitive = true
}

output "user" {
  value = "oauth2"
}

output "image_path" {
  value = "registry.gitlab.com/${gitlab_project.project.path_with_namespace}"
}

output "project_id" {
  value = tostring(gitlab_project.project.id)
}
