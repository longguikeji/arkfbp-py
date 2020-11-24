"""
serializer
"""
from arkfbp.executer import Executer
# pylint: disable=line-too-long
from arkfbp.node import FunctionNode
from ...modeling import get_api_config, collect_model_mapping, get_serializer_node


# Editor your node here.
class SerializerCore(FunctionNode):
    """
    it will generate all serializer nodes and field nodes dynamically,
    finally return the result to the siteapi flow.
    """
    def run(self, *args, **kwargs):
        """
        initialize a master serializer node,
        then run this master node to validate request params,
        finally may run the handler function to contact with DB.
        """
        try:
            print('Initializing master serializer node...')
            _, api_detail = get_api_config(self.inputs.method, self.flow.api_config)
            self.intervene(api_detail)
            # api_detail => {"name":"create_user", "type":"create", "request":{}, "response":{}}
            serializer_node = get_serializer_node(api_detail['request'], self.flow.config)
            print('Done!')
            # 数据校验
            print('Running master serializer node...')
            outputs = Executer.start_node(serializer_node, self.flow)
            print('Done!')
            if not self.flow.valid_status():
                return outputs
            print('Running handle function...')
            # 获取涉及到的所有原生model的class list
            model_mapping = collect_model_mapping(api_detail['request'], self.flow.config)
            # TODO 从相应的validated_data中获取指定model的字段值，然后每个model进行handler的处理
            ret = serializer_node.handle(api_detail, model_mapping, *args, **kwargs)
            print('Done!')
            return ret
        # pylint: disable=broad-except
        except Exception as exception:
            return self.flow.shutdown(exception.__str__(), response_status=500)

    def intervene(self, api_detail):
        """
        Change some properties of flow to interfere with the flow direction.
        """
        # debug or not
        self.flow.debug = api_detail.get('debug', True)
