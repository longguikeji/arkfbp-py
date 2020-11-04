"""
serializer
"""
import time

from arkfbp.executer import Executer
from arkfbp.node import FunctionNode, CharFieldNode, IntegerFieldNode, FloatFieldNode
from arkfbp.node import ModelSerializerNode
from arkfbp.utils.util import json_load

FIELD_MAPPING = {
    'string': CharFieldNode,
    'integer': IntegerFieldNode,
    'float': FloatFieldNode,
    'model_object': ModelSerializerNode,
}

API_TYPE_MAPPING = {
    'create': 'create',
    'delete': 'delete',
    'update': 'update',
    'retrieve': 'retrieve',
}


# Editor your node here.
class SerializerCore(FunctionNode):
    """
    it will generate all serializer nodes and field nodes dynamically,
    finally return the result to the siteapi flow.
    """
    serializer_handler = ModelSerializerNode

    def run(self, *args, **kwargs):
        """
        initialize a master serializer node,
        then run this master node to validate request params,
        finally may run the handler function to contact with DB.
        """
        try:
            print('Initializing master serializer node...')
            _, api_detail = self.get_api_config(self.inputs.method.upper())
            self.intervene(api_detail)

            serializer_node = self.get_serializer_node(api_detail, self.flow.config)
            print('Done!')
            # 数据校验
            print('Running master serializer node...')
            outputs = Executer.start_node(serializer_node, self.flow)
            print('Done!')
            if not self.flow.valid_status():
                return outputs
            print('Running handle function...')
            handler, api_detail = self.get_api_config(self.inputs.method.upper())
            ret = serializer_node.handle(handler, api_detail, *args, **kwargs)
            print('Done!')
            return ret
        # pylint: disable=broad-except
        except Exception as exception:
            return self.flow.shutdown(exception.__str__(), response_status=500)

    def get_serializer_node(self, api_detail, config, serializer_handler=None):
        """
        Dynamically generate serializer node with
        field node which in request_config and response.
        Both of api_detail and config are not necessarily in the same file,
        because of model_object field exists.
        """
        cls_name = 'Serializer_%s' % str(time.time()).replace(".", "")
        cls_attr = {}
        for field in api_detail['request']:
            cls_attr.update({field: self.get_field_node(field, config)})
        cls_attr.update({'model_path': config['model'], 'api_detail': api_detail, 'config': config})
        cls = type(cls_name, (serializer_handler or self.serializer_handler, ), cls_attr)
        return cls()

    def get_field_node(self, field, config):
        """
        generate a field node by field name and config data.
        """
        field_type, field_detail = get_field_config(field, config)
        field_cls = FIELD_MAPPING[field_type]
        # TODO 对field_detail中的信息进行合法性校验

        if field_type == 'model_object':
            # get serializer node
            config = json_load(field_detail['config_path'])
            return self.get_serializer_node(field_detail, config)
        return field_cls(**field_detail)

    def get_api_config(self, method):
        """
        get api config by request http method.
        """
        for api_type, api_detail in self.flow.api_config.items():
            if api_detail['http_method'] == method:
                return api_type, api_detail

        raise Exception(f'No api config for http_method:{method}!')

    def intervene(self, api_detail):
        """
        Change some properties of flow to interfere with the flow direction.
        """
        # debug or not
        self.flow.debug = api_detail.get('debug', True)


def get_field_config(field, config):
    """
    get field type and field detail by field name and meta config
    """
    field_type = list(config['meta'][field]['type'].keys())[0]
    field_detail = config['meta'][field]['type'][field_type]
    return field_type, field_detail
