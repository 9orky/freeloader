variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "ami" {
  type    = string
  default = ""
}

variable "key_name" {
  type    = string
  default = "freeloader"
}

variable "ssh_public_key" {
  type    = string
  default = ""
}
