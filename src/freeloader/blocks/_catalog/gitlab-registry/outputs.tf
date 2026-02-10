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
