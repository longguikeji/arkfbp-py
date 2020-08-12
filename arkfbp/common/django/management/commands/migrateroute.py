import json
import os
from json.decoder import JSONDecodeError
from os import path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Migrate route information from the form arkfbp to the native form django"

    def handle(self, **options):
        route_dir = path.join(os.getcwd(), '.arkfbp', 'routes')

        # Iterate through the entire folder
        for root, dirs, files in os.walk(route_dir):

            for filename in files:
                if not filename.endswith('.json'):
                    # Ignore some files as they cause various breakages.
                    continue

                filepath = path.join(root, filename)
                with open(filepath, 'r', encoding='utf8') as route_file:
                    # print('这是读取到文件数据的数据类型：', type(json_data))
                    try:
                        route_info = json.load(route_file)
                    except JSONDecodeError:
                        raise CommandError(f'{filepath} Decoding Error!')

                    self.validate_route(filepath, route_info)
                    print('route_info is', route_info)

    def validate_route(self, filepath, route_info: dict):
        """validate the data from the json file"""
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

