from rest_framework.versioning import URLPathVersioning


class CustomUrlPathVersioning(URLPathVersioning):
    version_param = "version"
    allowed_versions = ("v1",)
