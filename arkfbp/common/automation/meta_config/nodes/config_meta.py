"""
Meta Config
"""
import os

from arkfbp.common.automation.admin.nodes.serializer import SERIALIZER_FIELD_MAPPING, FIELD_CONFIG_MAPPING
from arkfbp.node import FunctionNode

# Editor your node here.
from arkfbp.utils.util import json_load, get_class_from_path


class ConfigMeta(FunctionNode):
    """
    return frontend a meta json data.
    """
    def run(self, *args, **kwargs):
        """
        run.
        """
        name = kwargs.get('meta_name', None)
        if not name:
            return self.flow.shutdown({'error': 'Invalid MetaName!'}, response_status=400)

        meta = self.get_meta(name)
        try:
            meta = self.merge_meta(meta)
        # pylint: disable=broad-except
        except Exception as exception:
            print('exception is', exception)
            return self.flow.shutdown(exception.__str__(), response_status=500)

        return meta

    def get_meta(self, name):
        """
        get meta data.
        """
        for root, _, files in os.walk(self.flow.file_dir):
            for file in files:
                if file.endswith('.json'):
                    data = json_load(os.path.join(root, file))
                    if data['name'] == name:
                        return data
        return self.flow.shutdown({'error': 'Meta Not Exists!'}, response_status=400)

    # pylint: disable=protected-access
    def merge_meta(self, meta):
        """
        merge data
        """
        modules = meta.pop('module')
        _meta = {meta.pop('name'): meta}
        for meta_name, detail in modules.items():
            if 'meta' in detail.keys():
                # meta config
                file_path = os.getcwd()
                for item in detail['meta'].split('.'):
                    file_path = os.path.join(file_path, item)
                file_path = f'{file_path}.json'
                slave_meta = json_load(file_path)
                module_meta = self.merge_meta(slave_meta)
                _meta.update(**module_meta)

            if 'model' in detail.keys():
                # model config
                module_model = {meta_name: {"type": "", "meta": {}, "api": {}}}

                # module_model = {"name": meta_name, "type": "", "meta": {}, "api": {}}
                cls = get_class_from_path(detail['model'])
                for item in cls._meta.fields:
                    field_type = SERIALIZER_FIELD_MAPPING[item.__class__]
                    field_config = {'title': item.verbose_name, 'type': {FIELD_CONFIG_MAPPING[field_type]: {}}}
                    module_model[meta_name]['meta'].update(**{item.name: field_config})
                _meta.update(**module_model)

        return _meta
