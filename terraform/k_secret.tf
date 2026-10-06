resource "aws_secretsmanager_secret" "kroger" {
  name        = "wad/kroger-api"
  description = "Kroger API credentials for Where's A Deal"
}