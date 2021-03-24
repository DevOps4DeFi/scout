## Note, to make things understandable, all code uses locals
## All variables should be mapped to locals in vars_to_locals.tf
## Other locals can go here too, or in-line with code when it makes sense

variable "aws_keypair_name" {
  type        = string
  description = "The name of the ssh keypair to use in order to allow access."
}

variable "app_name" {
  type        = string
  description = "The name of the application that will be used for tagging."
  default     = "scout"
}
variable "route53_root_fqdn" {
  type        = string
  description = "Root route53 domain name that we should build records on top of."
}
variable "region" {
  type        = string
  description = "The aws region to deploy into."
  default     = "us-east-1"
}
variable "public_subnet_ids" {
  type        = list(string)
  default     = null
  description = "A list of public subnets in the vpc, if null use default vpc."
}
variable "private_subnet_ids" {
  type        = list(string)
  default     = null
  description = "A list of public subnets in the vpc, if null use default vpc."
}
variable "vpc_id" {
  type        = string
  default     = null
  description = "The VPC to deploy into, if null use default vpc."
}
variable "tags" {
  default = {
    terraform = "yes"
    git_repo  = "https://github.com/Badger-Finance/scout"
  }
}
variable "ethnode_url_ssm_parameter_name" {
  type        = string
  description = "The URL of an eth node for scout-collector to pull blocks from"
}

variable "bsc_url_ssm_parameter_name" { ## TODO: make optional
  type        = string
  description = "The URL of an eth node for scout-collector to pull blocks from"
}
variable "scout_docker_image" {
  default = null
}
variable "grafana_docker_image" {
  default = null
}
variable "prometheus_docker_image" {
  default = null
}
variable "instance_type" {
  default = "t2.micro"
}
variable "datavolume_size" {
  default     = "25"
  description = "The amount of storage in gb for prometheus and grafana state"
}

variable "grafana_admin_password_ssm_name" {
  default = "/DevOps4DeFi/grafana_admin_password"
}

variable "ebs_snapshot_id" {
  default = null
  description = "The Snapshot id of a snapshot volume from a prior scout instance"
}

variable "public_lb_https_listener_arn" {
  type=string
  description = "The arn to an https alb listener that will be used for load balancing public facing services"
}
variable "public_lb_name" {
  type=string
  description = "The name of the public alb running the specified listener"
}
variable "public_lb_sg_id" {
  type = string
  description = "The id of a security group that the public alb is in"
}
variable "private_lb_https_listener_arn" {
  type=string
  description = "The arn to an https alb listener that will be used for load balancing private facing services"
}
variable "private_lb_name" {
  type=string
  description = "The name of the private alb running the specified listener"
}
variable "private_lb_sg_id" {
  type = string
  description = "The id of a security group that the private alb is in"
}

variable "disable_instance_termination" {
  default = true
  description = "Set to false to allow the instance to be terminated, make sure you take a snapshot of your data volume first"
}

variable "ssm_base" {
  default = "/DevOps4Defi"
  description = "a path followed by a where this module should output new ssm parameters"
}

variable "root_domain_wildcard_acm_cert_arn" {
  type=string
  description = "An arn to a wildcard cert for the root domain."
}

variable "create_ecr" {
  default = true
}