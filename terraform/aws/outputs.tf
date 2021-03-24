output "scout_ecr_url" {
  value = try(aws_ecr_repository.scout[0].repository_url, null)
}
output "grafana_ecr_url" {
  value = try(aws_ecr_repository.grafana[0].repository_url, null)
}
output "prometheus_ecr_url" {
  value = try(aws_ecr_repository.prometheus[0].repository_url, null)
}
