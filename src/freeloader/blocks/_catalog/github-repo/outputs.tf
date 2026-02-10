output "repo_name" {
  value = github_repository.repo.full_name
}

output "clone_url" {
  value = github_repository.repo.ssh_clone_url
}
