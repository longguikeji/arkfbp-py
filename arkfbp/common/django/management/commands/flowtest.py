import os

from arkfbp.flow.executer import FlowExecuter
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run all Arkfbp Test Flows"

    def handle(self, **options):
        FlowExecuter.start_all_test_flows(os.getcwd())

    def add_arguments(self, parser):
        pass
