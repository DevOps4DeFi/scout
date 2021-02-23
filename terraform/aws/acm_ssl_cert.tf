`resource "aws_acm_certificate" "https" {
  domain_name       = "*.${data.aws_route53_zone.rootzone.name}"
  validation_method = "DNS"
  tags              = var.tags
  subject_alternative_names = [
  data.aws_route53_zone.rootzone.name]
  /*
  lifecycle {
    create_before_destroy = true
  }
  */
}

resource "aws_route53_record" "acm-validation" {
  for_each = {
    for dvo in aws_acm_certificate.https.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
  } }
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.rootzone.zone_id
}

resource "aws_acm_certificate_validation" "https" {
  certificate_arn         = aws_acm_certificate.https.arn
  validation_record_fqdns = [for record in aws_route53_record.acm-validation : record.fqdn]
}
