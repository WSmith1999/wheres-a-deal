output "ec2_public_ip" {
  description = "Public IP address of the WAD EC2 instance"
  value       = module.ec2_instance.public_ip
}

output "rds_endpoint" {
  description = "RDS PostgreSQL hostname"
  value       = module.db.db_instance_address
}

output "rds_secret_arn" {
  description = "ARN of the RDS master credentials secret"
  value       = module.db.db_instance_master_user_secret_arn
}

output "kroger_secret_arn" {
  description = "ARN of the Kroger API credentials secret"
  value       = aws_secretsmanager_secret.kroger.arn
}

output "sns_topic_arn" {
  description = "SNS topic used for price alerts"
  value       = module.sns.topic_arn
}