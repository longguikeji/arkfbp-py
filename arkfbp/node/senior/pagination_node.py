"""
PaginationNode for view flow
"""
from collections import OrderedDict

from django.core.paginator import Paginator as DjangoPaginator

from ..function_node import FunctionNode
from ...utils.urls import replace_query_param, remove_query_param


class PaginationNode(FunctionNode):
    """
    Pagination Node
    self.input == model_queryset
    """
    paginator_class = DjangoPaginator
    page_size = 10
    page_query_param = 'page'

    def run(self, *args, **kwargs):
        queryset = self.paginate_queryset(**kwargs)
        handler = kwargs.get('handler', None)
        if handler:
            data = handler(queryset)
            return self.get_paginated_response(data, **kwargs)
        return self.flow.shutdown({'error': 'PaginationNode Return Nothing!'}, response_status=400)

    def paginate_queryset(self, **kwargs):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(page_size=kwargs.get('page_size', None))
        if not page_size:
            return None
        paginator = self.paginator_class(self.inputs, page_size)
        page_number = kwargs.get('page', 1)
        # pylint: disable=attribute-defined-outside-init
        self.page = paginator.page(page_number)
        return list(self.page)

    def get_paginated_response(self, data, **kwargs):
        """
        get paginated response
        """
        return OrderedDict([('count', self.page.paginator.count),
                            ('next', self.get_next_link(kwargs.get('request', None))),
                            ('previous', self.get_previous_link(kwargs.get('request', None))), ('results', data)])

    def get_page_size(self, page_size=None):
        """
        get page size
        """
        if page_size is not None:
            return page_size

        return self.page_size

    def get_next_link(self, request):
        """
        get next page link
        """
        if not all((request, self.page.has_next())):
            return None
        url = request.build_absolute_uri()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self, request):
        """
        get previous page link
        """
        if not all((request, self.page.has_previous())):
            return None
        url = request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)
