/*
ECS Service
*/
data "aws_iam_policy_document" "ecs_service_assumerole" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "ecs.amazonaws.com",
        "s3.amazonaws.com",
      ]
    }
  }
}


resource "aws_iam_role" "ecs_service" {
  name_prefix               = "ecsServiceRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_service_assumerole.json
  tags               = var.tags
}

resource "aws_iam_policy" "ecs-service" {
  name_prefix = "ecsService"
  policy = file("${path.module}/iam_policies/ecsServicePolicy.json")
}
resource "aws_iam_role_policy_attachment" "ecs_service_main_policy" {
  count = var.create_ecr == true ? 1 : 0
  role   = aws_iam_role.ecs_service.id
  policy_arn = aws_iam_policy.scout-reader[0].arn
}

/*
ECS Task
*/
data "aws_iam_policy_document" "ecs_task_assumerole" {
  version = "2012-10-17"
  statement {
    sid     = ""
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecs_exec" {
  statement {
    effect    = "Allow"
    resources = ["*"]

    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecs:DescribeTaskDefinition",
      "ecs:ListServices",
      "ecs:DescribeServices",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "ssm:GetParameter", ##TODO consider limiting scope of ssm parameter access per app
      "ssm:GetParameters",
      "ssm:GetParameterHistory",
      "ssm:GetParametersByPath",
    ]
  }
}

// AWS IAM Role used for ecs task execution
resource "aws_iam_role" "ecs_exec" {
  name               = "ecsExecTaskRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assumerole.json
  tags               = var.tags
}

// AWS IAM Role Policy used for ecs task execution
resource "aws_iam_role_policy" "ecs_exec" {
  name   = "ecsExecRolePolicy"
  policy = data.aws_iam_policy_document.ecs_exec.json
  role   = aws_iam_role.ecs_exec.id
}