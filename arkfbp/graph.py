class GraphNode:

    def __init__(self, node):
        pass


class Graph:

    def __init__(self):
        self._nodes = []

    def get_node_by_id(self, id):
        for node in self._nodes:
            if node['id'] == id:
                return node

        raise Exception('node id not found {}'.format(id))

    def add(self, node):
        self._nodes.append(node)
        return self

    def get_entry_node(self):
        if len(self._nodes) == 0:
            return None

        for node in self._nodes:
            if node.kind == 'start':
                return node

        return self._nodes[0]

    def nodes(self):
        return self._nodes