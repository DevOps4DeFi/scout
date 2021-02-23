locals {
  vpc_id   = var.vpc_id == null ? aws_default_vpc.default[0].id : var.vpc_id
  vpc_cidr = var.vpc_id == null ? aws_default_vpc.default[0].cidr_block : data.aws_vpc.vpc[0].cidr_block
  subnets  = var.private_subnet_ids == null ? [for aws_subnet in aws_default_subnet.default : aws_subnet.id] : var.private_subnet_ids
}


resource "aws_default_subnet" "default" {
  for_each          = var.public_subnet_ids == null ? toset(["a", "b", "c"]) : [] ##  Use first 3 azs, don't run if subnets are passed in
  availability_zone = "${var.region}${each.value}"
}

resource "aws_default_vpc" "default" {
  count = var.vpc_id == null ? 1 : 0
}

data "aws_vpc" "vpc" {
  count = var.vpc_id == null ? 0 : 1
  id    = var.vpc_id
}


