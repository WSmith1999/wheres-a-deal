module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "wad-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-2a", "us-east-2b", "us-east-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

}

module "ec2_instance" {
  source = "terraform-aws-modules/ec2-instance/aws"

  name = "wad-ec2"
  ami  = data.aws_ami.amazon_linux.id

  instance_type               = var.ec2_instance_type
  key_name                    = aws_key_pair.wad_key.key_name
  monitoring                  = false
  subnet_id                   = module.vpc.public_subnets[0]
  create_security_group       = false
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name



  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

resource "aws_key_pair" "wad_key" {
  key_name   = "wad-key"
  public_key = file("C:/Users/naras/.ssh/wad-key.pub")
}

module "db" {
  source = "terraform-aws-modules/rds/aws"

  identifier = "wad-db"

  engine            = "postgres"
  engine_version    = "18.3"
  family            = "postgres18"
  instance_class    = "db.t4g.micro"
  allocated_storage = 20

  db_name  = "waddb1"
  username = "will"
  port     = 5432

  manage_master_user_password         = true
  iam_database_authentication_enabled = false

  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  # DB subnet group
  create_db_subnet_group = true
  subnet_ids             = module.vpc.private_subnets

  deletion_protection = false
  skip_final_snapshot = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }

}


module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "pricecheck"
  description   = "Lambda price checker"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.lambda_sg.id]
  environment_variables = {
    SNS_TOPIC_ARN     = module.sns.topic_arn
    DB_SECRET_ARN     = module.db.db_instance_master_user_secret_arn
    DB_HOST           = module.db.db_instance_address
    DB_NAME           = "waddb1"
    DB_PORT           = "5432"
    KROGER_SECRET_ARN = aws_secretsmanager_secret.kroger.arn
  }

  create_role = false
  lambda_role = aws_iam_role.lambda_role.arn

  create_package         = false
  local_existing_package = "../lambda_package_zip.zip"
  timeout                = 30
}

module "sns" {
  source = "terraform-aws-modules/sns/aws"

  name = "pricealerts"

  subscriptions = {
    email = {
      protocol = "email"
      endpoint = var.alert_email
    }
  }
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus = false

  attach_lambda_policy = true
  lambda_target_arns   = [module.lambda_function.lambda_function_arn]

  schedules = {
    lambda-cron = {
      description         = "Trigger Lambda Price check"
      schedule_expression = "rate(1 day)"
      timezone            = "America/New_York"
      arn                 = module.lambda_function.lambda_function_arn
    }
  }
}

