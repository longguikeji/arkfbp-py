"""
Meta Config
"""
import os

from arkfbp.node import FunctionNode
from arkfbp.utils.util import json_load
from ...modeling import merge_meta, CONFIG_NAME
# Editor your node here.


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
            meta = merge_meta(meta)
        # pylint: disable=broad-except
        except Exception as exception:
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
                    if data[CONFIG_NAME] == name:
                        return data
        return self.flow.shutdown({'error': 'Meta Not Exists!'}, response_status=400)
