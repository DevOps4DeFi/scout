resource "aws_security_group" "public_alb_sg" {
  name_prefix = "${var.app_name}_public_alb"
  vpc_id      = local.vpc_id
  tags        = var.tags
  ingress {
    from_port   = 443
    protocol    = "TCP"
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
    description = "Grafana from world"
  }
  ingress {
    from_port   = 9090
    protocol    = "TCP"
    to_port     = 9090
    cidr_blocks = ["0.0.0.0/0"]
    description = "Prometheus - need private alb for security"
  }
  egress {
    from_port   = 0
    protocol    = "-1"
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
  lifecycle {
    create_before_destroy = true
  }
}
#
# Security Group
#

resource "aws_security_group" "ecs_instance" {
  name_prefix        = "${var.app_name}-ecs-ec2"
  description = "${var.app_name} instance security group"
  vpc_id      = local.vpc_id
  tags        = merge({ Name = "${var.app_name}-ec2-cluster" }, var.tags)
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "ecs_instance_egress" {
  description       = "All outbound"
  security_group_id = aws_security_group.ecs_instance.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "ecs_instance_public_alb" {
  security_group_id = aws_security_group.ecs_instance.id
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
source_security_group_id = var.public_lb_sg_id
description = "ephemeral ports for bridge mode lb"
}
resource "aws_security_group_rule" "ecs_instance_private_alb" {
  security_group_id = aws_security_group.ecs_instance.id
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  source_security_group_id = var.private_lb_sg_id
  description = "ephemeral ports for bridge mode lb"
}
resource "aws_security_group_rule" "ecs_instance_own_vpc" {
  security_group_id = aws_security_group.ecs_instance.id
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks = [local.vpc_cidr]
  description = "ephemeral ports for bridge mode lb"
}

resource "aws_security_group_rule" "ecs-instance-self" {
  security_group_id = aws_security_group.ecs_instance.id
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  self =  true
  description = "ephemeral ports for bridge mode lb"
}


