from django.core.files.storage import FileSystemStorage
from storages.backends.s3 import S3Storage


class PrivateFileSystemStorage(FileSystemStorage):
    def url(self, name):
        raise ValueError("Document files are available only through protected views.")


class PrivateS3Storage(S3Storage):
    def url(self, name, parameters=None, expire=None, http_method=None):
        raise ValueError("Document files are available only through protected views.")
