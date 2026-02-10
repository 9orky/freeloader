provider "aws" {
  region = var.region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "deployer" {
  count      = var.ssh_public_key != "" ? 1 : 0
  key_name   = "${var.key_name}-freeloader"
  public_key = var.ssh_public_key
}

resource "aws_security_group" "instance" {
  name = "freeloader-${var.key_name}-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "server" {
  ami                    = var.ami != "" ? var.ami : data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.ssh_public_key != "" ? aws_key_pair.deployer[0].key_name : var.key_name
  vpc_security_group_ids = [aws_security_group.instance.id]

  tags = {
    Name       = "freeloader-${var.key_name}"
    ManagedBy  = "freeloader"
  }
}
