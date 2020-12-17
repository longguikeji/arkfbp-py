import os

from common.django.drf.utils import convert_directory_configs_to_models
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "generate model files"

    def handle(self, **options):
        current_path = os.path.abspath(os.path.curdir)
        config_path = '/'.join( options.get('models').split('.'))
        real_path = os.path.join(current_path, config_path)
        model_path = os.path.dirname(real_path)
        lines = convert_directory_configs_to_models(real_path)
        model_filename = os.path.join(model_path, 'models.py')
        with open(model_filename, 'w') as model_file:
            model_file.write('\n'.join(lines))


    def add_arguments(self, parser):
        parser.add_argument('--models', type=str, help='Specifies the import path for the target flow name.')
