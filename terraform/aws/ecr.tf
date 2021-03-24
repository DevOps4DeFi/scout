resource "aws_ecr_repository" "prometheus" {
  count = var.create_ecr == true ? 1 : 0
  name = "prometheus"
}
resource "aws_ecr_repository" "scout" {
  count = var.create_ecr == true ? 1 : 0
  name = "scout"
}
resource "aws_ecr_repository" "grafana" {
  count = var.create_ecr == true ? 1 : 0
  name = "grafana"
}
locals {
  all_repo_arns = var.create_ecr ? [aws_ecr_repository.grafana[0].arn, aws_ecr_repository.scout[0].arn, aws_ecr_repository.prometheus[0].arn] : []
}
resource "aws_iam_user" "scout-deployer" {
  count = var.create_ecr == true ? 1 :0
  name = "${var.app_name}-deployer"
}
data "aws_iam_policy_document" "scout-reader" {
  statement {
    sid = "AllAcountsRead"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:DescribeRepositories"]
    resources = [for repoarn in local.all_repo_arns: "${repoarn}/*"]
  }
}
data "aws_iam_policy_document" "scout-deployer" {
  statement {
    sid = "DoDockerLogin"
    actions = [
      "ecr:GetAuthorizationToken"]
    resources = [
      "*"]
  }
  statement {
    sid = "PushPullECR"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeRepositories"]
      resources = [for repoarn in local.all_repo_arns: "${repoarn}*"]
  }
}
resource "aws_iam_policy" "scout-deployer" {
  count = var.create_ecr == true ? 1 :0
  name_prefix = "scout-deployer"
  policy = data.aws_iam_policy_document.scout-deployer.json
  lifecycle {
    create_before_destroy = true
  }
}
resource "aws_iam_policy" "scout-reader" {
  count = var.create_ecr == true ? 1 :0
  name_prefix = "scout-reader"
  policy = data.aws_iam_policy_document.scout-reader.json
  lifecycle {
    create_before_destroy = true
  }
}
resource "aws_iam_user_policy_attachment" "scout-deployer" {
  count = var.create_ecr == true ? 1 :0
  policy_arn = aws_iam_policy.scout-deployer[0].arn
  user = aws_iam_user.scout-deployer[0].name
}
resource "aws_iam_access_key" "scout-deployer" {
  count = var.create_ecr == true ? 1 :0
  user = aws_iam_user.scout-deployer.name
}
resource "aws_ssm_parameter" "scout-deployer-access-key" {
  count = var.create_ecr == true ? 1 :0
  name = "${var.ssm_base}/terraform-out/scout-deployer-aws-access-key"
  type = "String"
  value = aws_iam_access_key.scout-deployer[0].id
}
resource "aws_ssm_parameter" "scout-deployer-access-secret" {
  count = var.create_ecr == true ? 1 :0
  name = "${var.ssm_base}/terraform-out/scout-deployer-aws-access-secret"
  type = "String"
  value = aws_iam_access_key.scout-deployer[0].secret
}