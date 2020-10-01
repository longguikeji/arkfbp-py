import os

from django.core.management.base import BaseCommand

from arkfbp.executer import Executer


class Command(BaseCommand):
    help = "Run all Arkfbp Test Flows"

    def handle(self, **options):
        Executer.start_testflows(os.getcwd())

    def add_arguments(self, parser):
        pass
