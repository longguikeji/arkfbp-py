import sys

from arkfbp.flow.executer import FlowExecuter
from django.test import TestCase

from .base import Node


class TestNode(TestCase, Node):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_outputs(self, flow, inputs, http_method=None, content_type=None, header=None):
        self.flow = flow
        self.inputs = inputs
        self.http_method = http_method
        self.content_type = content_type
        self.header = header
        return FlowExecuter.start_test_flow(self.flow, self.inputs, http_method=self.http_method,
                                            content_type=self.content_type, header=self.header)

    def run(self):
        self.setUp()

        through = []
        testList = list(filter(lambda m: m.startswith("test_") and callable(getattr(self, m)), dir(self)))
        for testcase in testList:
            try:
                getattr(self, testcase)()
                sys.stdout.write(testcase + ' is ok  \n')
                through.append(testcase)
            except Exception as e:
                sys.stdout.write(testcase + ' failed  \n')
            continue

        self.tearDown()
        print('-----------------------------------------\n')
        print('测试用例有：' + str(len(testList)) + '\n')
        print('通过用例数为：' + str(len(through)) + '\n')
        print('失败用例数为：' + str(len(testList) - len(through)) + '\n')
