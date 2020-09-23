import json
import os
import time
from json.decoder import JSONDecodeError
from os import path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template import Engine, Context

import arkfbp
from arkfbp.common.api_visualization import DjangoVisualApi


class Command(BaseCommand):
    help = "Migrate route information from the form arkfbp to the native form django"

    def add_arguments(self, parser):
        parser.add_argument('--topdir', type=str, help='Specify the parent directory where ArkFBP resides.')
        parser.add_argument('--urlfile', type=str, help='Specify the destination file for the migration.')

    def handle(self, **options):
        """
        By default, the ArkFBP folder is found in the same directory as the
        project configuration file Settings.py. If the ArkFBP folder is not
        in the same parent directory as settings.py, you need to manually
        specify the directory where ArkFBP is located.
        """
        default_top_dir = settings.ARKFBP_CONF if hasattr(settings, 'ARKFBP_CONF') else settings.SETTINGS_MODULE.rsplit('.', 1)[0]
        top_dir = options.get('topdir')
        if not top_dir:
            top_dir = default_top_dir
        route_dir = path.join(top_dir, 'arkfbp', 'routes')
        # Iterate through the entire folder
        modules_set, apis_set = [], []
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
                    modules, apis = self.load_api_context(json_routes, DjangoVisualApi)
                    apis_set.extend(apis)
                    modules_set.extend(modules)
        url_file = options.get('urlfile')
        if not url_file:
            url_file = path.join(default_top_dir, 'auto_{}_migrate_urls.py'.format(
                time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            ))

        self.render(modules_set, apis_set, url_file)

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

    def load_api_context(self, routes_info: dict, handler: object):
        """
        Load the text information used to generate the django native urls.py file.
        """
        visual_api = handler(routes_info)
        return visual_api.generate_api_context()

    def render(self, modules_set, apis_set, file_path):
        """
        Render the text message to the urls.py file
        """
        if not apis_set:
            return

        api_text = ' ' + apis_set[0]
        for api in apis_set[1:]:
            api_text = f'{api_text},\n {api}'
        api_text = f'[\n{api_text}\n]'

        module_text = modules_set[0]
        for module in modules_set[1:]:
            module_text = f'{module_text}\n{module}'

        context = Context({
            'import_module': module_text,
            'routes_info': api_text,
        }, autoescape=False)

        old_path = path.join(arkfbp.common.django.__path__[0], 'conf', 'route_template', 'urls_name.py-tpl')
        with open(old_path, 'r', encoding='utf-8') as template_file:
            content = template_file.read()
        template = Engine().from_string(content)
        content = template.render(context)
        with open(file_path, 'w+', encoding='utf-8') as new_file:
            new_file.write(content)
