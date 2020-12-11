"""Process requests from django.

A flow is a django view which process request.
 We convert an interface in config.json to an APIView, and process requests with flows.
"""
from django.utils.decorators import classonlymethod
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet as ModelViewSetBase
from arkfbp.executer import Executer
from arkfbp.flow.base import Flow

class ViewsetMeta(type):
    """
    要用这个元类生成一个具有全部求值环境的ModelViewSet类
    """

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


class GeneralSerializer(serializers.ModelSerializer):

    class Meta:
        model = None

# pylint: disable=abstract-method
class ModelViewSet(Flow, ModelViewSetBase):
    """
    经过改造后的ModelViewSet基类。混合三个主要特性: Flow 的特性， 标准查改增删特性
    """

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        if self.serializer_class:
            return self.serializer_class
        else:
            GeneralSerializer.Meta.model = self.model
            return GeneralSerializer

    def dispatch(self, request, *args, **kwargs):
        """
        override django view function dispatch.
        """
        if request.method.lower() in self.allow_http_method:
            return Executer.start_flow(self, request, *args, **kwargs)

    @classmethod
    def set_http_method(cls, method: list):
        """
        set http method.
        """
        cls.allow_http_method = method

    @classonlymethod
    def as_view(cls, http_method=None, **initkwargs):
        """
        Before executing the as_view function, pass it the `allow_http_method`
        """
        if http_method:
            cls.set_http_method(http_method)
        #initkwargs.pop('suffix')
        return super().as_view(actions=http_method) # , **initkwargs)

    def shutdown(self, outputs, **kwargs):
        """
        shutdown the flow.
        """
        self.response_status = kwargs.get('response_status', self.response_status)
        super().shutdown(outputs)

    @property
    def response(self):
        """
        generate a http response.
        """
        return self.outputs

    @classonlymethod
    def get_urls(cls):
        return []