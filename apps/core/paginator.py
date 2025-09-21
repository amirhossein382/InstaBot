from django.core import paginator
from django.utils.functional import cached_property


class CustomModelAdminPaginator(paginator.Paginator):
    @cached_property
    def count(self):
        return 15
