resource "aws_cloudwatch_log_group" "scout" {
  name = "/ecs/${var.app_name}"
  tags = var.tags
}