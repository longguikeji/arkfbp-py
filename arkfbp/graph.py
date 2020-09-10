from cachetools import cached
from cachetools.keys import hashkey

from .node import IFNode, StartNode


class Graph:

    def __init__(self):
        self._graph_nodes = []

    def add(self, node):
        self._graph_nodes.append(node)
        return self

    @property
    def graph_nodes(self):
        return self._graph_nodes

    @graph_nodes.setter
    def graph_nodes(self, graph_nodes):
        self._graph_nodes = graph_nodes


class GraphNode:

    cls = None
    id = None
    next = None
    positive_next = None
    negative_next = None

    def __init__(self, graph_node, handler=None):
        self.graph_node = graph_node
        self.parse(handler)

    def parse(self, handler):
        # cls
        node_cls = self.graph_node.get('cls', None)
        if not node_cls:
            raise Exception('Invalid Graph Node,it must includes a cls')
        self.cls = node_cls

        # id
        node_id = self.graph_node.get('id', None)
        if node_id is None:
            raise Exception('node id must be settled')
        self.id = node_id

        # next
        if issubclass(node_cls, IFNode):
            positive_next_id = self.graph_node.get('positive_next', None)
            self.positive_next = handler.get_graph_node(positive_next_id) if positive_next_id else None
            negative_next_id = self.graph_node.get('negative_next', None)
            self.negative_next = handler.get_graph_node(negative_next_id) if negative_next_id else None
        else:
            next_id = self.graph_node.get('next', None)
            self.next = handler.get_graph_node(next_id) if next_id else None

    @property
    def instance(self):
        return self.cls()

    def next_graph_node(self, node_ret):
        if issubclass(self.cls, IFNode):
            graph_node = self.positive_next if node_ret else self.negative_next
        else:
            graph_node = self.next
        return graph_node


class GraphParser:

    def __init__(self, graph):
        self.graph = graph

    def parse_graph_node(self, _graph_node):
        graph_node = GraphNode(_graph_node, handler=self)
        return graph_node

    def get_graph_node(self, node_id):
        for graph_node in self.graph.graph_nodes:
            if graph_node['id'] == node_id:
                return graph_node

        raise Exception(f'Node ID:{node_id} not found')

    @cached(cache={}, key=lambda self: hashkey(self.graph))
    def get_entry_node(self):
        if len(self.graph.graph_nodes) == 0:
            return None

        for graph_node in self.graph.graph_nodes:
            _graph_node = self.parse_graph_node(graph_node)
            if _graph_node.cls.kind == StartNode.kind:
                return _graph_node.graph_node

        return self.graph.graph_nodes[0]
