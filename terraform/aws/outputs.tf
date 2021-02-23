output "scout_ecr_url" {
  value = aws_ecr_repository.scout.repository_url
}
output "grafana_ecr_url" {
  value = aws_ecr_repository.grafana.repository_url
}
output "prometheus_ecr_url" {
  value = aws_ecr_repository.prometheus.repository_url
}
