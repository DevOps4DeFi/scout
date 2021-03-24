data "aws_ami" "amazon_linux_ecs" {
  most_recent = true
  owners = [
  "amazon"]
  filter {
    name = "name"
    values = [
    "amzn2-ami-ecs-*"]
  }

    filter {
      name   = "architecture"
      values = ["x86_64"]
    }

    filter {
      name   = "virtualization-type"
      values = ["hvm"]
    }
}