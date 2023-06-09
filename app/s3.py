import boto3
import config
import enum
import io
import typing
import pathlib


class Namespace(enum.Enum):
    CLIPS = config.CLIPS_OBJECT_PREFIX
    PHRASES = config.PHRASES_OBJECT_PREFIX
    RAW = config.RAW_OBJECT_PREFIX


class S3ObjectKey:

    @staticmethod
    def create_object_key(namespace: Namespace, filename: str) -> 'S3ObjectKey':
        path = f"{namespace.value}/{filename}"
        return S3ObjectKey(namespace, path)

    def __init__(self, namespace: Namespace, path: str):
        self._bucket = config.BUCKET_NAME
        self._namespace = namespace
        self._path = pathlib.Path(path)

    def is_file(self) -> bool:
        return self.get_filestem() != self._namespace.value

    def get_bucket(self) -> str:
        return self._bucket
    
    def get_key(self) -> str:
        return self._path.as_posix()
    
    def get_filestem(self) -> str:
        return self._path.stem

    def get_extension(self) -> str:
        return self._path.suffix[1:]

    def __str__(self) -> str:
        return f"s3://{self._bucket}/{self._path}"


class S3:
    def __init__(self, namespace: Namespace):
        self._bucket = config.BUCKET_NAME
        self._namespace = namespace
        self._client = boto3.client("s3", config=config.botocore_config)
        self._s3 = boto3.resource("s3", config=config.botocore_config)

    def list_file_object_keys(self) -> typing.Generator[S3ObjectKey, None, None]:
        continuation_token = None
        has_object_keys = True
        while has_object_keys:
            object_key_prefix = f"{self._namespace.value}/"
            if continuation_token is None:
                response = self._client.list_objects_v2(Bucket=config.BUCKET_NAME,
                                                        Prefix=object_key_prefix,)
            else:
                response = self._client.list_objects_v2(Bucket=config.BUCKET_NAME,
                                                        Prefix=object_key_prefix,
                                                        ContinuationToken=continuation_token,)
            for content in response["Contents"]:
                s3_object_key = S3ObjectKey(namespace=self._namespace, path=content["Key"],)
                if s3_object_key.is_file():
                    yield s3_object_key
            continuation_token = response.get("NextContinuationKey")
            has_object_keys = continuation_token is not None

    def get_object_contents(self, object_key: S3ObjectKey) -> io.BytesIO:
        bytes_io = io.BytesIO()
        theobject = self._s3.Object(self._bucket, object_key.get_key())
        theobject.download_fileobj(bytes_io)
        return bytes_io

    def delete_object(self, object_key: S3ObjectKey) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=object_key.get_key(),)

    def put_object(self, object_key: S3ObjectKey, data: io.BytesIO) -> None:
        self._client.put_object(Body=data.read(), Bucket=self._bucket, Key=object_key.get_key())

    def copy(self, src_object_key: S3ObjectKey, dst_object_key: S3ObjectKey) -> None:
        self._client.copy(
            Bucket=self._bucket,
            CopySource={
                "Bucket": self._bucket,
                "Key": src_object_key.get_key(),
            },
            Key=dst_object_key.get_key(),
        )


if __name__ == "__main__":
    s3 = S3(Namespace.UNPROCESSED)
    for x in s3.list_file_object_keys():
        theobject = s3.S3Object(x)
        break

