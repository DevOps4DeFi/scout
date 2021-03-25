locals {
  grafana_docker_image = var.grafana_docker_image == null ? aws_ecr_repository.grafana[0].repository_url : var.grafana_docker_image
}

resource "aws_ecs_service" "grafana" {
  name            = "grafana"
  task_definition = aws_ecs_task_definition.grafana.id
  cluster         = aws_ecs_cluster.scout.name
  launch_type     = "EC2"
  desired_count   = 1
  tags            = var.tags
  load_balancer {
    container_name   = "grafana"
    container_port   = 3000
    target_group_arn = aws_lb_target_group.grafana.arn
  }
}

resource "aws_ecs_task_definition" "grafana" {
  family                   = "${var.app_name}-grafana"
  container_definitions = jsonencode(concat(
  jsondecode(module.grafana-container-definition.json_map_encoded_list),
  jsondecode(module.grafana-render-container-definition.json_map_encoded_list)))
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_exec.arn
  network_mode             = "bridge"
  volume {
    name      = "grafana-data"
    host_path = "${local.mount_point}/grafana-data"
  }
}

module "grafana-container-definition" {
  source                       = "cloudposse/ecs-container-definition/aws"
  version                      = "0.47.0"
  container_image              = local.grafana_docker_image ##TODO add versioning
  container_name               = "grafana"
  container_memory_reservation = 128
  links = ["renderer"]

  mount_points = [
    {
      containerPath = "/var/lib/grafana",
      sourceVolume  = "grafana-data"
    }
  ]
  log_configuration = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.scout.id
      awslogs-region        = var.region
      awslogs-stream-prefix = "grafana"
    }
  }
  secrets = [
    {
      name = "GF_SECURITY_ADMIN_PASSWORD"
      valueFrom = var.grafana_admin_password_ssm_name
    }
  ]
  environment = [
    {
      name = "GF_SERVER_ROOT_URL"
      value = "https://${aws_route53_record.grafana.fqdn}"
    },
    {
      name = "HOSTNAME"
      value = aws_route53_record.grafana.fqdn
    },
    {
      name ="GF_ROOT_URL"
      value = "https://${aws_route53_record.grafana.fqdn}"
    },
    {
      name  = "GF_RENDERING_CALLBACK_URL"
      value = "https://${aws_route53_record.grafana.fqdn}/"
    },
    {
      name  = "GF_LOG_FILTERS"
      value = "rendering:debug"
    },
    {
      name  = "PROMETHEUS_URL"
      value = "https://${aws_route53_record.prometheus.fqdn}:${var.prometheus_lb_port}"
    },
    {
      name = "GF_SECURITY_ADMIN_USER"
      value = "admin"
    },
     {
      name = "GF_AUTH_DISABLE_LOGIN_FORM"
      value = "false"
    },
    {
      name = "GF_AUTH_ANONYMOUS_ENABLED"
      value = "true"
    },
    {
      name = "GF_RENDERING_SERVER_URL"
      value = "http://renderer:8081/render"
    },
    {
      name = "GF_AUTH_ANONYMOUS_ORG_ROLE"
      value = "Viewer"
    }
  ]
  port_mappings = [
    {
      ## Main port
      containerPort = 3000
      hostPort = null
      protocol      = "tcp"
    }
  ]
}
module "grafana-render-container-definition" {
  source                       = "cloudposse/ecs-container-definition/aws"
  version                      = "0.47.0"
  container_image              = "grafana/grafana-image-renderer:latest" ##TODO add versioning
  container_name               = "renderer"
  container_memory_reservation = 64
  log_configuration = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.scout.id
      awslogs-region        = var.region
      awslogs-stream-prefix = "grafana-renderer"
    }
  }
  environment = [
    {
      name  = "ENABLE_METRICS"
      value = "true"
    },
    {
      name  = "HTTP_HOST"
      value = "0.0.0.0"
    }
  ]
  port_mappings = [
    {
      ## Main port
      containerPort = 8081
      hostPort = null
      protocol      = "tcp"
    }
  ]
}

resource "aws_lb_target_group" "grafana" {
  name        = "${var.app_name}-grafana"
  protocol    = "HTTP"
  port        = 3000
  target_type = "instance"
  vpc_id      = local.vpc_id
  tags = {
    name = "grafana"
  }
  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 6
    timeout             = 5
    interval            = 10
    path                = "/"
  }
}

## If so they need their own target groups.
resource "aws_lb_listener_rule" "https_grafana" {
  listener_arn = var.public_lb_https_listener_arn
  condition {
    host_header {
      values = [
        "${var.app_name}.${var.route53_root_fqdn}"]
    }
  }
    action {
      target_group_arn = aws_lb_target_group.grafana.arn
      type = "forward"
    }
}
