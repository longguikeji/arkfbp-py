import json
import os
from json.decoder import JSONDecodeError
from os import path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Migrate route information from the form arkfbp to the native form django"

    def add_arguments(self, parser):
        parser.add_argument('--topdir', type=str, help='Specify the parent directory where ArkFBP resides.')

    def handle(self, **options):
        """
        By default, the ArkFBP folder is found in the same directory as the
        project configuration file Settings.py. If the ArkFBP folder is not
        in the same parent directory as settings.py, you need to manually
        specify the directory where ArkFBP is located.
        """
        # route_dir = path.join(os.getcwd(), 'arkfbp', 'routes')
        top_dir = options.get('topdir')
        print('topdir is', top_dir)
        if top_dir:
            route_dir = top_dir
        else:
            default_top_dir = settings.SETTINGS_MODULE.rsplit('.', 1)[0]
            default_route_dir = path.join(default_top_dir, 'arkfbp', 'routes')
            route_dir = default_route_dir
            print('default_top_dir is', default_top_dir)
            print('default_route_dir is', default_route_dir)
        # Iterate through the entire folder
        url_set = []
        for root, dirs, files in os.walk(route_dir):
            for filename in files:
                if not filename.endswith('.json'):
                    # Ignore some files as they cause various breakages.
                    continue

                filepath = path.join(root, filename)
                with open(filepath, 'r', encoding='utf8') as route_file:
                    try:
                        json_routes = json.load(route_file)
                    except JSONDecodeError:
                        raise CommandError(f'{filepath} Decoding Error!')

                    self.validate_route(filepath, json_routes)
                    print('route_info is', json_routes)
                    urls = self.load_urls(json_routes)
                    url_set.extend(urls)

    def validate_route(self, filepath, route_info: dict):
        """
        validate the data from the json file.
        """
        # verify the existence of the required parameters
        required_params = ['namespace', 'routes']
        for param in required_params:
            if param not in route_info.keys():
                raise CommandError(f'{filepath} Invalid! {required_params} is required.')

        # verify the type of value
        if not isinstance(route_info['namespace'], str):
            raise CommandError(f'{filepath} Invalid! namespace must be string.')

        if not isinstance(route_info['routes'], list):
            raise CommandError(f'{filepath} Invalid! routes must be list.')

    def load_urls(self, routes):
        """
        load url info through JSON data.
        """
        return ""
