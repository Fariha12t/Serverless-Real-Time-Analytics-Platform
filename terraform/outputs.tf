output "api_ingest_url" {
  description = "POST events to this URL"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/events"
}

output "api_query_url" {
  description = "GET KPIs from this URL"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/kpis"
}

output "kinesis_stream_name" {
  description = "Kinesis stream name"
  value       = aws_kinesis_stream.events.name
}

output "dynamodb_table_name" {
  description = "DynamoDB KPI table"
  value       = aws_dynamodb_table.kpis.name
}

output "s3_data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "athena_workgroup" {
  description = "Athena workgroup name"
  value       = aws_athena_workgroup.main.name
}
