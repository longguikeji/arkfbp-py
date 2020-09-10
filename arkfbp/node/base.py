from abc import abstractmethod


# Node metadata
_NODE_ID = ''
_NODE_NAME = 'base'
_NODE_KIND = 'base'


class Node:

    id = _NODE_ID
    name = _NODE_NAME
    kind = _NODE_KIND
    next = None
    error_next = None

    def __init__(self, *args, **kwargs):
        self._state = None
        self._inputs = None
        self._outputs = None
        self._flow = None

    def __str__(self):
        return f'Node: {self.id}:({self.name}:{self.kind})'

    def __repr__(self):
        return f'ID:{self.id} Kind:{self.kind} Class:{self.__class__}'

    def commit_state(self, cb):
        """
        commit state
        """
        self.state = cb(self.state)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def flow(self):
        return self._flow

    @flow.setter
    def flow(self, flow):
        self._flow = flow

    @abstractmethod
    def run(self, *args, **kwargs):
        """run a node"""
        raise NotImplementedError

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, inputs):
        self._inputs = inputs

    def on_completed(self, *args, **kwargs):
        """overridden by user"""

    def on_error(self, *args, **kwargs):
        """overridden by user"""

    def created(self, *args, **kwargs):
        """overridden by user"""

    def before_initialize(self, *args, **kwargs):
        """overridden by user"""

    def init(self, *args, **kwargs):
        """overridden by user"""

    def initialized(self, *args, **kwargs):
        """overridden by user"""

    def before_execute(self, *args, **kwargs):
        """overridden by user"""

    def executed(self, *args, **kwargs):
        """overridden by user"""

    def before_destroy(self, *args, **kwargs):
        """overridden by user"""
