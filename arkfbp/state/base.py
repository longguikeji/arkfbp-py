import copy


class State:
    """
    Used to record global information for the duration of a workflow.

    steps: {
            node.id: node,
            ...,
        }
    """
    def __init__(self, init_data=None):
        self._nodes = []
        self._data = copy.deepcopy(init_data) if init_data else {}
        self._steps = {}

    @property
    def nodes(self):
        """A list of all the nodes that have been run."""
        return self._nodes

    def push(self, node):
        """Press the target node into state nodes."""
        self._nodes.append(node)
        self._steps[node.id] = node

    def pop(self):
        """Pop the target node from the State nodes."""
        if not len(self._nodes):
            return None

        node = self._nodes.pop()
        return node

    def fetch(self):
        """fetch state data"""
        return self._data

    def commit(self, data):
        """merge state data"""
        self._data = {**self._data, **data}

    @property
    def steps(self):
        return self._steps
