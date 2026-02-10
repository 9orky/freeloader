provider "gitlab" {}

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
  name       = "freeloader-registry-token"
  scopes     = var.token_scopes
  expires_at = formatdate("YYYY-MM-DD", timeadd(timestamp(), "8760h"))
}
