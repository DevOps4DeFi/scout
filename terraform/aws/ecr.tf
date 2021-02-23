locals {
  name_suffix = var.app_name == "scout"? "" : "-${var.app_name}"
}
resource "aws_ecr_repository" "prometheus" {
  name = "prometheus${local.name_suffix}"
}
resource "aws_ecr_repository" "scout" {
  name = "scout${local.name_suffix}"
}
resource "aws_ecr_repository" "grafana" {
  name = "grafana${local.name_suffix}"
}
locals {
  all_repo_arns = [aws_ecr_repository.grafana.arn, aws_ecr_repository.scout.arn, aws_ecr_repository.prometheus.arn]
}
resource "aws_iam_user" "scout-deployer" {
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
  name_prefix = "${var.app_name}-deployer"
  policy = data.aws_iam_policy_document.scout-deployer.json
  lifecycle {
    create_before_destroy = true
  }
}
resource "aws_iam_policy" "scout-reader" {
  name_prefix = "${var.app_name}-reader"
  policy = data.aws_iam_policy_document.scout-reader.json
  lifecycle {
    create_before_destroy = true
  }
}
resource "aws_iam_user_policy_attachment" "scout-deployer" {
  policy_arn = aws_iam_policy.scout-deployer.arn
  user = aws_iam_user.scout-deployer.name
}
resource "aws_iam_access_key" "scout-deployer" {
  user = aws_iam_user.scout-deployer.name
}
resource "aws_ssm_parameter" "scout-deployer-access-key" {
  name = "${var.ssm_base}/terraform-out/${var.app_name}-deployer-aws-access-key"
  type = "String"
  value = aws_iam_access_key.scout-deployer.id
}
resource "aws_ssm_parameter" "scout-deployer-access-secret" {
  name = "${var.ssm_base}/terraform-out/scout-deployer-aws-access-secret"
  type = "String"
  value = aws_iam_access_key.scout-deployer.secret
}