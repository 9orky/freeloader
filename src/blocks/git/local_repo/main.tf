variable "remote_url" {
  type    = string

  validation {
    condition = can(regex("^(https?|git|ssh|rsync|file)://", var.remote_url))
    error_message = "The remote_url (${var.remote_url}) must be a valid Git URL."
  }
}

variable "target_folder" {
  type    = string

  validation {
    condition = direxists(var.target_folder)
    error_message = "The target_folder (${var.target_folder}) must exist."
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