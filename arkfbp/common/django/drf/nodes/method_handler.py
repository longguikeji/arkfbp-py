"""
Permission Core Nodes
"""
from arkfbp.node import FlowNode


class HandlerCore(FlowNode):
    """
    permission core node.
    """
    from common.django.drf.flows.list_handler import ListHandler
    from common.django.drf.flows.retrieve_handler import RetrieveHandler
    from common.django.drf.flows.create_handler import CreateHandler
    from common.django.drf.flows.update_handler import UpdateHandler
    from common.django.drf.flows.destroy_handler import DestroyHandler
    list_handler = ListHandler()
    create_handler = CreateHandler()
    retrieve_handler = RetrieveHandler()
    update_handler = UpdateHandler()
    destroy_handler = DestroyHandler()
    dispatcher = {
        'list': list_handler,
        'retrieve': retrieve_handler,
        'create': create_handler,
        'update': update_handler,
        'partial_update': update_handler,
        'destroy': destroy_handler
    }

    def get_child_flow(self, *args, **kwargs):
        return self.dispatcher[self.flow.action]


