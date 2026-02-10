provider "github" {
  owner = var.org
}

resource "github_repository" "repo" {
  name        = var.name
  visibility  = var.visibility
  description = var.description
  has_issues  = true
  has_wiki    = false
}

resource "github_branch_protection" "main" {
  count               = var.protect_main ? 1 : 0
  repository_id       = github_repository.repo.node_id
  pattern             = "main"
  enforce_admins      = true
  allows_deletions    = false
  allows_force_pushes = false
  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = false
    required_approving_review_count = 1
  }
}

resource "github_actions_secret" "registry_user" {
  count           = var.registry_user != "" ? 1 : 0
  repository      = github_repository.repo.name
  secret_name     = "REGISTRY_USER"
  plaintext_value = var.registry_user
}

resource "github_actions_secret" "registry_token" {
  count           = var.registry_token != "" ? 1 : 0
  repository      = github_repository.repo.name
  secret_name     = "REGISTRY_TOKEN"
  plaintext_value = var.registry_token
}

resource "github_actions_secret" "registry_host" {
  count           = var.registry_host != "" ? 1 : 0
  repository      = github_repository.repo.name
  secret_name     = "REGISTRY_HOST"
  plaintext_value = var.registry_host
}

resource "github_actions_secret" "registry_image_path" {
  count           = var.registry_image_path != "" ? 1 : 0
  repository      = github_repository.repo.name
  secret_name     = "REGISTRY_IMAGE_PATH"
  plaintext_value = var.registry_image_path
}

resource "github_actions_secret" "deploy_webhook_url" {
  count           = var.deploy_webhook_url != "" ? 1 : 0
  repository      = github_repository.repo.name
  secret_name     = "DEPLOYMENT_WEBHOOK_URL"
  plaintext_value = var.deploy_webhook_url
}
