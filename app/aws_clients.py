import boto3

from app.settings import get_settings


def get_boto3_client(service_name: str):
    settings = get_settings()
    return boto3.client(
        service_name,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def get_boto3_resource(service_name: str):
    settings = get_settings()
    return boto3.resource(
        service_name,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
