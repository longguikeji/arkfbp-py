"""
Test Node
"""
import sys

from django.test import TestCase

from arkfbp.executer import Executer
from .base import Node


class TestNode(TestCase, Node):
    """
    Test Node
    """
    def setUp(self):
        """
        set up function
        """

    def tearDown(self):
        """
        teardown function
        """

    # pylint: disable=attribute-defined-outside-init
    def get_outputs(self, flow, inputs, http_method=None, content_type=None, header=None):
        """
        get outputs
        """
        self.flow = flow
        self.inputs = inputs
        self.http_method = http_method
        self.content_type = content_type
        self.header = header
        return Executer.start_testflow(self.flow,
                                       self.inputs,
                                       http_method=self.http_method,
                                       content_type=self.content_type,
                                       header=self.header)

    # pylint: disable=unused-argument, signature-differs
    def run(self, *args, **kwargs):
        self.setUp()

        through = []
        test_list = list(filter(lambda m: m.startswith("test_") and callable(getattr(self, m)), dir(self)))
        for testcase in test_list:
            try:
                getattr(self, testcase)()
                sys.stdout.write(testcase + ' is ok  \n')
                through.append(testcase)
            # pylint: disable=broad-except, unused-variable
            except Exception as exception:
                sys.stdout.write(testcase + ' failed  \n')
            continue

        self.tearDown()
        print('-----------------------------------------\n')
        print('测试用例有：' + str(len(test_list)) + '\n')
        print('通过用例数为：' + str(len(through)) + '\n')
        print('失败用例数为：' + str(len(test_list) - len(through)) + '\n')
