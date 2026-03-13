terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
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

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "machine_type" {
  type    = string
  default = "e2-micro"
}

variable "disk_size_gb" {
  type    = number
  default = 30
}

variable "image_family" {
  type    = string
  default = "debian-12"
}

variable "image_project" {
  type    = string
  default = "debian-cloud"
}

variable "network" {
  type    = string
  default = "default"
}

variable "subnetwork" {
  type    = string
  default = ""
}

variable "ssh_user" {
  type    = string
  default = "freeloader"
}

variable "ssh_public_key" {
  type    = string
  default = ""
}

variable "ssh_source_ranges" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

locals {
  service_account  = jsondecode(var.gcp_service_account_json)
  project_id       = trimspace(var.project_id) != "" ? trimspace(var.project_id) : local.service_account.project_id
  name_parts       = regexall("[a-z0-9]+", lower(var.name))
  trimmed_name     = length(local.name_parts) > 0 ? join("-", local.name_parts) : ""
  instance_name    = trimsuffix(substr("vm-${local.trimmed_name != "" ? local.trimmed_name : "instance"}", 0, 63), "-")
  firewall_name    = trimsuffix(substr("ssh-${local.trimmed_name != "" ? local.trimmed_name : "instance"}", 0, 63), "-")
  instance_tag     = trimsuffix(substr("ssh-${local.trimmed_name != "" ? local.trimmed_name : "instance"}", 0, 63), "-")
  should_generate  = trimspace(var.ssh_public_key) == ""
  authorized_key   = local.should_generate ? trimspace(tls_private_key.generated[0].public_key_openssh) : trimspace(var.ssh_public_key)
  private_key_path = local.should_generate ? local_file.generated_private_key[0].filename : ""
  startup_script = templatefile("${path.module}/templates/startup.sh.tftpl", {
    ssh_user       = var.ssh_user
    ssh_public_key = local.authorized_key
  })
}

provider "google" {
  credentials = var.gcp_service_account_json
  project     = local.project_id
  zone        = var.zone
}

data "google_compute_image" "base" {
  family  = var.image_family
  project = var.image_project
}

resource "tls_private_key" "generated" {
  count     = local.should_generate ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "generated_private_key" {
  count           = local.should_generate ? 1 : 0
  content         = tls_private_key.generated[0].private_key_pem
  filename        = "${path.module}/${local.instance_name}.pem"
  file_permission = "0600"
}

resource "google_compute_firewall" "ssh" {
  name    = local.firewall_name
  project = local.project_id
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = [local.instance_tag]
}

resource "google_compute_instance" "vm" {
  name                = local.instance_name
  project             = local.project_id
  zone                = var.zone
  machine_type        = var.machine_type
  deletion_protection = false
  tags                = [local.instance_tag]

  boot_disk {
    initialize_params {
      image = data.google_compute_image.base.self_link
      size  = var.disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    network    = trimspace(var.subnetwork) == "" ? var.network : null
    subnetwork = trimspace(var.subnetwork) != "" ? trimspace(var.subnetwork) : null

    access_config {}
  }

  metadata = {
    enable-oslogin = "FALSE"
    ssh-keys       = "${var.ssh_user}:${local.authorized_key}"
  }

  metadata_startup_script = local.startup_script

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  depends_on = [google_compute_firewall.ssh]
}

output "ip_address" {
  value = google_compute_instance.vm.network_interface[0].access_config[0].nat_ip
}

output "instance_id" {
  value = tostring(google_compute_instance.vm.instance_id)
}

output "ssh_user" {
  value = var.ssh_user
}

output "public_dns" {
  value = google_compute_instance.vm.network_interface[0].access_config[0].nat_ip
}

output "ssh_private_key_path" {
  value     = local.private_key_path
  sensitive = true
}