terraform {}

variable "remote_url" {
  type = string
  default = "file://here"

  validation {
    condition     = can(regex("^(https?|git|ssh|rsync|file)://", var.remote_url))
    error_message = "The remote_url must be a valid Git URL (https, git, ssh, rsync, or file scheme)."
  }
}

variable "target_folder" {
  type = string

  validation {
    condition     = length(var.target_folder) > 0
    error_message = "The target_folder must not be empty."
  }
}

resource "terraform_data" "git_local_repo_setup" {
  triggers_replace = [
    var.target_folder,
    var.remote_url
  ]

  provisioner "local-exec" {
    working_dir = var.target_folder
    command     = <<EOT
      git init
      git remote add origin ${var.remote_url}
      git branch -M main
    EOT
  }
}