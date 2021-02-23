## TODO re-add conditionally if no public ALB is provided
/*resource "aws_lb" "public_alb" {
  name               = "scout-public-alb"
  load_balancer_type = "application"
  subnets            = local.subnets
  security_groups    = [aws_security_group.public_alb_sg.id]
  internal           = false
  tags = merge(var.tags,
    {
      Name = "scout_public_alb"
  })
}
*/
data "aws_lb" "public_alb" {
    name = var.public_lb_name
}
data "aws_lb" "private_alb" {
    name = var.private_lb_name
}