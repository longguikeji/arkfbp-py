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
    page_size_query_param = 'page_size'
    count_param = 'count'
    next_param = 'next'
    previous_param = 'previous'
    results_param = 'results'
    serializer_node = None

    def run(self, *args, **kwargs):
        self.page_query_param = kwargs.get('page_query_param', self.page_query_param)
        self.page_size_query_param = kwargs.get('page_size_query_param', self.page_size_query_param)
        self.count_param = kwargs.get('count_param', self.count_param)
        self.next_param = kwargs.get('next_param', self.next_param)
        self.previous_param = kwargs.get('previous_param', self.previous_param)
        self.results_param = kwargs.get('results_param', self.results_param)

        self.serializer_node = kwargs.get('serializer_node')
        if not self.serializer_node:
            return self.flow.shutdown({'error': 'PaginationNode Has No SerializerNode!'}, response_status=400)

        data = self.handle_queryset(self.serializer_node, self.paginate_queryset(**kwargs))
        paginated_response = kwargs.get('paginated_response')
        if paginated_response:
            return paginated_response(self, data, **kwargs)

        return self.get_paginated_response(data, **kwargs)

    def paginate_queryset(self, **kwargs):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        # pylint: disable=attribute-defined-outside-init
        page_size = self.get_page_size(page_size=kwargs.get('page_size', None))
        if not page_size:
            return None
        paginator = self.paginator_class(self.inputs, page_size)
        self.page_number = kwargs.get('page', 1)
        self.page_size = page_size
        # pylint: disable=attribute-defined-outside-init
        self.page = paginator.page(self.page_number)
        return list(self.page)

    # pylint: disable=no-self-use
    def handle_queryset(self, serializer_node, queryset):
        """
        handle queryset.
        iterator instances => dict data.
        """
        return serializer_node.to_representation(queryset)

    def get_paginated_response(self, data, **kwargs):
        """
        get paginated response
        """

        return OrderedDict([(self.page_query_param, self.page_number), (self.page_size_query_param, self.page_size),
                            (self.count_param, self.page.paginator.count),
                            (self.next_param, self.get_next_link(kwargs.get('request'))),
                            (self.previous_param, self.get_previous_link(kwargs.get('request'))),
                            (self.results_param, data)])

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
