#!/bin/sh
set -eu

QUEUE_NAME="${SQS_QUEUE_NAME:-events-queue}"
TABLE_NAME="${DYNAMODB_TABLE_NAME:-events-table}"

echo "Provisioning SQS queue: ${QUEUE_NAME}"
if ! awslocal sqs get-queue-url --queue-name "${QUEUE_NAME}" >/dev/null 2>&1; then
  awslocal sqs create-queue --queue-name "${QUEUE_NAME}" >/dev/null
fi

echo "Provisioning DynamoDB table: ${TABLE_NAME}"
if ! awslocal dynamodb describe-table --table-name "${TABLE_NAME}" >/dev/null 2>&1; then
  awslocal dynamodb create-table \
    --table-name "${TABLE_NAME}" \
    --attribute-definitions AttributeName=event_id,AttributeType=S \
    --key-schema AttributeName=event_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST >/dev/null
fi

echo "LocalStack resources are ready."
