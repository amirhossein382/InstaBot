from rest_framework.views import APIView
from rest_framework import status as rest_status
from rest_framework.response import Response

from apps.core.utils import Logger
from apps.core.utils.instagram_client.exceptions import InstagramError
from apps.account.exceptions import base_response_with_error
from .services import DownloaderService

_logger = Logger()
_downloader_svc = DownloaderService()


class DownloaderUrlResolverAPIView(APIView):
    def get(self, _, url, **kwargs):
        account = self.request.user.instagram_account
        try:
            resolved_url: dict = _downloader_svc.resolve_media_url(account, url)
        except InstagramError as exc:
            status_code = getattr(exc, 'status_code', 500)
            return base_response_with_error(msg=str(exc), _status=status_code)
        except Exception as exc:
            err_class = exc.__class__.__name__
            _logger.log_event(
                self.__class__.__name__,
                log_data=f"{err_class} exception while media resolving! :{str(exc)}", level="WARNING",
            )
            return base_response_with_error(msg="Failed to resolve media url!",
                                            _status=rest_status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data=resolved_url, status=rest_status.HTTP_200_OK)
