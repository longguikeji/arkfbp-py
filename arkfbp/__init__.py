from .nodes import (Node, StartNode, StopNode, FunctionNode, NopNode, APINode, IFNode, LoopNode)

from .graph import (Graph, GraphNode)

from .state import (State, FlowState, AppState)

from .stack import Stack

from .flow import Flow, ViewFlow

from arkfbp.response import Response

from .utils.version import get_version

VERSION = (0, 0, 2, 'alpha', 0)
__version__ = get_version()

# def int_or_str(value):
#     try:
#         return int(value)
#     except ValueError:
#         return value
# import importlib


# def run_flow(flowname, inputs):
#     filename = '.'.join(['flows', flowname, 'main'])
#     clz = importlib.import_module(filename)
#     instance = clz.Main()
#     return instance.main(inputs)

# def run_flow(flow, request):
#     flow = 'flows.{}.main'.format(flow,)
#     mod = __import__(flow)
#     secs = flow.split('.')

#     for s in secs[1:]:
#         mod = getattr(mod, s)

#     f = mod.Main()
#     if hasattr(f, 'created'):
#         f.created()

#     # f.state.request = request
#     # f.state.data_dir = ''

#     inputs = request.get_json()

#     if hasattr(f, 'before_initialize'):
#         f.before_initialize()

#     f.init()

#     if hasattr(f, 'initialized'):
#         f.initialized()

#     if hasattr(f, 'before_execute'):
#         f.before_execute()

#     ret = f.main(inputs=inputs)

#     if hasattr(f, 'executed'):
#         f.executed()

#     if hasattr(f, 'before_destroy'):
#         f.before_destroy()

#     if ret is None:
#         return ''

#     return ret
