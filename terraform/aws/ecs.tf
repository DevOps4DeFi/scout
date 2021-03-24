resource "aws_ecs_cluster" "scout" {
  name = var.app_name
}