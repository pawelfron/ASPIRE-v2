from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = "Initialize MinIO bucket"

    def handle(self, *args, **options):
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION_NAME,
            use_ssl=settings.S3_USE_SSL,
            verify=settings.S3_VERIFY,
        )

        bucket_name = settings.S3_STORAGE_BUCKET_NAME

        try:
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(
                self.style.SUCCESS(f'Bucket "{bucket_name}" already exists')
            )
        except ClientError:
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created bucket "{bucket_name}"')
                )
            except ClientError as e:
                self.stdout.write(self.style.ERROR(f"Error creating bucket: {e}"))
