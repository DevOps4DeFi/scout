#
# EC2
#
locals {
  mount_point = "/data" # the mount point for the ebs volume
}
resource "aws_instance" "main" {
  iam_instance_profile        = aws_iam_instance_profile.ecs_instance_profile.name
  instance_type               = var.instance_type
  ami                         = data.aws_ami.amazon_linux_ecs.id
  disable_api_termination     = var.disable_instance_termination
  associate_public_ip_address = false ## can change if there is a nat gateway]
  subnet_id                   = local.subnets[0]
  monitoring                  = true
  vpc_security_group_ids      = [aws_security_group.ecs_instance.id]
  key_name                    = var.aws_keypair_name
  user_data = templatefile("${path.module}/templates/userdata.template.sh", {
    ebs_device_name = "/dev/xvdf"
    cluster_name    = aws_ecs_cluster.scout.name
    mount_point     = local.mount_point
  })
  tags = merge(var.tags, {
    Name = "${var.app_name}_ecs_data"
  })
  lifecycle {
    ignore_changes = [ami, user_data]
  }
  ebs_block_device {
    device_name           = "/dev/xvdf"
    volume_type           = "gp2"
    volume_size           = var.datavolume_size
    snapshot_id = var.ebs_snapshot_id
    delete_on_termination = false
  }
  ebs_block_device {
    ## docker volumes mount provided as part of ami
    device_name = "/dev/xvdcz"
  }
}
###
# IAM
###
data "aws_iam_policy_document" "ecs_instance_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_instance_role" {
  name               = "ecs-instance-role-${var.app_name}"
  assume_role_policy = data.aws_iam_policy_document.ecs_instance_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
resource "aws_iam_role_policy_attachment" "SSMManagement" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "ecsInstanceRole-${var.app_name}"
  path = "/"
  role = aws_iam_role.ecs_instance_role.name
}

