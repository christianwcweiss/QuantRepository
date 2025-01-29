provider "aws" {
  region = "eu-west-1"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


resource "aws_s3_bucket" "layer_bucket" {
    bucket = "alpha-rai-lambda-layer-${data.aws_caller_identity.current.account_id}-${lower(var.environment)}"
}

resource "aws_s3_bucket" "strategies_bucket" {
    bucket = "alpha-rai-strategies-results-${lower(var.environment)}"
}

module "quant_core_layer" {
  depends_on = [
    aws_s3_bucket.layer_bucket
  ]
  source = "../modules/quant_core_layer"

  layer_name         = "quant_core_layer_${lower(var.environment)}"
  layers_bucket_name = aws_s3_bucket.layer_bucket.bucket
}

# ---------------------- ORCHESTRATOR LAMBDA --------------------------------

resource "aws_sns_topic_policy" "orchestrator_lambda_signals_policy" {
  arn = aws_sns_topic.orchestrator_lambda_signals_topic.arn

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = "*",
        Action = "sns:Publish",
        Resource = aws_sns_topic.orchestrator_lambda_signals_topic.arn,
        Condition = {
          StringEquals = {
            "AWS:SourceOwner" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_sns_topic" "orchestrator_lambda_signals_topic" {
  name = "orchestrator_lambda_topic_${lower(var.environment)}"
}


module "orchestrator_lambda" {
  source = "../modules/technical/lambda"

  alerts_topic_arn  = "arn:aws:sns:eu-west-1:${data.aws_caller_identity.current.account_id}:${aws_sns_topic.orchestrator_lambda_signals_topic.name}"
  environment       = var.environment
  handler           = "handler.handle"
  name              = "orchestrator_lambda_${lower(var.environment)}"
  source_path = "${path.module}/../../code/lambdas/orchestrator"
  layers = [
     module.quant_core_layer.lambda_layer_arn,
  ]
  environment_vars = {
    ENVIRONMENT = upper(var.environment)
    IG_API_KEY = jsondecode(data.aws_secretsmanager_secret_version.ig_api_secrets_version.secret_string)["IG_API_KEY"]
    IG_USERNAME = jsondecode(data.aws_secretsmanager_secret_version.ig_api_secrets_version.secret_string)["IG_USERNAME"]
    IG_PASSWORD = jsondecode(data.aws_secretsmanager_secret_version.ig_api_secrets_version.secret_string)["IG_PASSWORD"]
    IG_ACCOUNT_ID = jsondecode(data.aws_secretsmanager_secret_version.ig_api_secrets_version.secret_string)["IG_ACCOUNT_ID"]
    DISCORD_USERNAME = "Alpha Rai 🤖"
    DISCORD_WEBHOOK_URL_ALERT = jsondecode(data.aws_secretsmanager_secret_version.discord_webhook_secrets_version.secret_string)["DISCORD_WEBHOOK_URL_ALERT"]
    SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:${data.aws_caller_identity.current.account_id}:${aws_sns_topic.orchestrator_lambda_signals_topic.name}"
  }
}

resource "aws_lambda_function_url" "orchestrator_lambda_url" {
  function_name      = module.orchestrator_lambda.function_name
  authorization_type = "NONE"
}

resource "aws_iam_role_policy" "orchestrator_lambda_iam_policy" {
  name   = "orchestrator_lambda_policy_${lower(var.environment)}"
  role   = module.orchestrator_lambda.role_name
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "sns:Publish"
        ],
        Resource = aws_sns_topic.orchestrator_lambda_signals_topic.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "orchestrator_lambda_iam_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = module.orchestrator_lambda.role_name
}

resource "aws_lambda_permission" "allow_public" {
    statement_id  = "FunctionURLAllowPublicAccess"
    action        = "lambda:InvokeFunctionUrl"
    function_url_auth_type = "NONE"
    function_name = module.orchestrator_lambda.function_name
    principal     = "*"
}

# ---------------------- TRADER LAMBDA --------------------------------
resource "aws_iam_role" "trader_lambda_role" {
  name = "trader-iam-lambda-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_policy" "trader_lambda_policy" {
  name = "trader-iam-lambda-policy-${var.environment}"
  description = "Policy for trader lambda"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "sns:Receive"
        ],
        Resource = aws_sns_topic.orchestrator_lambda_signals_topic.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "trader_lambda_policy_attachment" {
  policy_arn = aws_iam_policy.trader_lambda_policy.arn
  role       = aws_iam_role.trader_lambda_role.name
}

# ---------------------- IG CLEANER LAMBDA --------------------------------
# TBD
