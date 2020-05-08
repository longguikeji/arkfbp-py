from abc import abstractmethod
import copy


class Node:

    id = ''
    name = ''
    kind = 'base'

    def __init__(self, *args, **kwargs):
        self._state = None
        self._inputs = None
        self._outputs = None
        self._flow = None

    def init(self):
        pass

    def commit_state(self, cb):
        '''
        commit state
        '''
        self.state = cb(self.state)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, v):
        self._state = v

    @property
    def flow(self):
        return self._flow

    @flow.setter
    def flow(self, v):
        self._flow = v

    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, v):
        self._outputs = v

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, v):
        self._inputs = v

    next = None
    error_next = None

    def on_completed(self):
        pass

    def on_error(self):
        pass

    def created(self):
        pass

    def before_initialized(self):
        pass

    def initialized(self):
        pass

    def before_execute(self):
        pass

    def executed(self):
        pass

    def before_destroy(self):
        pass