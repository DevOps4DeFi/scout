data "aws_ami" "amazon_linux_ecs" {
  most_recent = true
  owners = [
  "amazon"]
  filter {
    name = "name"
    values = [
    "amzn-ami-*-amazon-ecs-optimized"]
  }
  filter {
    name = "owner-alias"
    values = [
    "amazon"]
  }
}