variable "project_name" {
  description = "Prefix for all AWS resources"
  type        = string
  default     = "analytics"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "kinesis_shard_count" {
  description = "Number of Kinesis shards (1 shard = ~1MB/s or 1000 records/s)"
  type        = number
  default     = 2
}

variable "dynamodb_billing" {
  description = "DynamoDB billing mode: PAY_PER_REQUEST or PROVISIONED"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "s3_data_lake_prefix" {
  description = "S3 key prefix for raw events"
  type        = string
  default     = "events"
}

variable "lambda_memory_mb" {
  description = "Lambda memory in MB"
  type        = number
  default     = 256
}

variable "lambda_timeout_sec" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}
