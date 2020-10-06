"""
Ast and code convert to each other
"""
import ast
from typing import Any

import astunparse
from django.core.management import CommandError
from yapf.yapflib.yapf_api import FormatCode

IMPORT_FROM = 'ImportFrom'
FUNCTION_DEF = 'FunctionDef'
RETURN = 'Return'
STR = 'Str'
NODE_DEFINE = ['cls', 'id', 'next', 'x', 'y']


class BaseTransformer(ast.NodeTransformer):
    """Base Transformer"""

    def generic_visit(self, node):
        """super generic_visit()"""
        super(BaseTransformer, self).generic_visit(node)
        return node

    def handle(self, node):
        """
        This contains the execution order of the processing nodes
        """
        return node

    def execute(self, file):
        """
        ast <=> code
        """
        r_node = self.parse_code(file)
        r_node = self.handle(r_node)
        self.parse_ast(r_node, file)
        return r_node

    def parse_code(self, file):
        """parse code into ast"""
        with open(file, 'r') as f:
            node = ast.parse(f.read())
        return node

    def parse_ast(self, node, file):
        """
        unparse code into ast
        """
        code_body = astunparse.unparse(node)
        with open(file, 'w') as f:
            # reformat a string of code
            reformatted_source, _ = FormatCode(code_body, file, style_config='pep8')
            f.write(reformatted_source)

    def valid_node(self, node: ast.Dict):
        """
        Check that the node information in the diagram conforms to the specification
        """
        if len(node.keys) != len(NODE_DEFINE):
            raise CommandError(f'Run failed, Invalid graph.Each node must have these five properties:{NODE_DEFINE}')

        for idx, key in enumerate(node.keys):
            if key.s != NODE_DEFINE[idx]:
                raise CommandError(
                    f'Run failed, Invalid graph.Each node must have these five properties in order:{NODE_DEFINE}')

    def process_NameConstant(self, param):
        """
        Automatically identify the conforming node and convert it to None node
        """
        if param == 'undefined' or param is None:
            return ast.NameConstant(value=None)

        if type(param) is str:
            return ast.Str(s=param)

        if type(param) is float:
            return ast.Num(n=param)


class AddNodeTransformer(BaseTransformer):
    """
    Add-Node Transformer
    """

    def __init__(self, clz, node_id, next_node_id=None, coord_x=None, coord_y=None, clz_as=None):
        _ = clz.split('.')
        self.module = '.'.join(_[:-1])
        self.clz = _[-1]
        self.clz_as = clz_as
        self.node_id = node_id
        self.next_node_id = next_node_id
        self.coord_x = coord_x
        self.coord_y = coord_y

    def visit_Module(self, node: ast.Module) -> Any:
        """
        visit module
        """
        # Remove Duplicates
        for idx, x in enumerate(node.body):
            if type(x).__name__ == IMPORT_FROM:
                if x.module == self.module:
                    for y in x.names:
                        if y.name == self.clz and y.asname == self.clz_as:
                            return node
            # add a ImportFrom Node
            new_node = ast.ImportFrom(module=self.module, names=[ast.alias(name=self.clz, asname=self.clz_as)], level=0)
            node.body.insert(idx, new_node)
            return node

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """
        visit class def
        """
        clz = 'Main'
        base_clz = 'ViewFlow'
        func_name = 'create_nodes'
        self.clz = self.clz_as if self.clz_as else self.clz
        if node.name == clz and node.bases[0].id == base_clz:
            for x in node.body:
                if type(x).__name__ == FUNCTION_DEF and x.name == func_name:
                    for y in x.body:
                        if type(y).__name__ == RETURN:
                            # check the node ID for duplicates
                            for z in y.value.elts:
                                # valid node
                                self.valid_node(z)
                                # update node
                                if z.values[1].s == self.node_id:
                                    raise CommandError('Run failed, duplicate node id')

                            dict_node = ast.Dict(keys=[
                                ast.Str(s='cls'),
                                ast.Str(s='id'),
                                ast.Str(s='next'),
                                ast.Num(n='x'),
                                ast.Num(n='y')
                            ],
                                values=[
                                    ast.Name(id=self.clz, ctx=ast.Load()),
                                    ast.Str(s=self.node_id),
                                    self.process_NameConstant(self.next_node_id),
                                    ast.Num(n=self.coord_x),
                                    ast.Num(n=self.coord_y),
                                ])

                            # try update relate node info
                            for idx, item in enumerate(y.value.elts):
                                try:
                                    if item.values[2].s and item.values[2].s == self.next_node_id:
                                        item.values[2].s = self.node_id
                                except AttributeError:
                                    continue

                            # insert target node info
                            if self.next_node_id:
                                for idx, item in enumerate(y.value.elts):
                                    if self.next_node_id == item.values[1].s:
                                        y.value.elts.insert(idx, dict_node)
                                        break
                            else:
                                y.value.elts.append(dict_node)
                            break
                    break

        return node

    def handle(self, node):
        """
        Override the parent class handler
        """
        node = self.visit_Module(node)
        node = self.generic_visit(node)
        return node


class UpdateNodeTransformer(BaseTransformer):
    """
    update node Transformer
    """
    rm_old_clz = False
    old_clz = None

    def __init__(self, clz, node_id, next_node_id=None, coord_x=None, coord_y=None, clz_as=None):
        self.module = None
        self.clz = None
        if clz:
            _ = clz.split('.')
            self.module = '.'.join(_[:-1])
            self.clz = _[-1]
        self.clz_as = clz_as
        self.node_id = node_id
        self.next_node_id = next_node_id
        self.coord_x = coord_x
        self.coord_y = coord_y

    def visit_Module(self, node: ast.Module) -> Any:
        """
        visit module
        更新导入包的路径：
            1）删除旧的导入路径。
            2）添加新的导入路径。
            3）更改当前导入路径。
        """
        # remove old import?
        _idx_1 = None
        _idx_2 = None
        if self.rm_old_clz and self.old_clz:
            for idx_x, x in enumerate(node.body):
                if type(x).__name__ == IMPORT_FROM:
                    for idx_y, y in enumerate(x.names):
                        if y.asname and y.asname == self.old_clz:
                            _idx_2 = idx_y
                            break
                        elif not y.asname and y.name == self.old_clz:
                            _idx_2 = idx_y
                            break
                    if _idx_2 is not None:
                        del x.names[_idx_2]
                        _idx_1 = idx_x if not x.names else None
                        break

            if _idx_1 is not None:
                del node.body[_idx_1]

        # update clz
        if self.clz:
            same_clz = False
            for idx, x in enumerate(node.body):
                if type(x).__name__ == IMPORT_FROM:
                    if x.module == self.module:
                        for y in x.names:
                            # 1) same import, update alias
                            if y.name == self.clz:
                                same_clz = True
                                y.asname = self.clz_as if self.clz_as else y.asname
                                break
                # 2) different import, add new import
                elif not same_clz:
                    new_node = ast.ImportFrom(module=self.module,
                                              names=[ast.alias(name=self.clz, asname=self.clz_as)],
                                              level=0)
                    node.body.insert(idx, new_node)
                    break

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """
        visit class def
        """
        clz = 'Main'
        base_clz = 'ViewFlow'
        func_name = 'create_nodes'
        if node.name == clz and node.bases[0].id == base_clz:
            for x in node.body:
                if type(x).__name__ == FUNCTION_DEF and x.name == func_name:
                    for y in x.body:
                        if type(y).__name__ == RETURN:
                            for z in y.value.elts:
                                # valid node
                                self.valid_node(z)
                                # update node
                                if z.values[1].s == self.node_id:
                                    # class
                                    old_clz = z.values[0].id
                                    if self.clz and self.clz != old_clz:
                                        self.rm_old_clz = True
                                        self.old_clz = old_clz
                                        z.values[0].id = self.clz
                                    elif self.clz_as and self.clz_as != old_clz:
                                        z.values[0].id = self.clz_as
                                    # id
                                    if self.next_node_id:
                                        z.values[2] = self.process_NameConstant(self.next_node_id)
                                    # coord x
                                    if self.coord_x:
                                        z.values[3] = ast.Num(n=self.coord_x)
                                    # coord y
                                    if self.coord_y:
                                        z.values[4] = ast.Num(n=self.coord_y)
                                    break
                            break
                    break

        return node

    def handle(self, node):
        """
        Override the parent class handler
        """
        node = self.generic_visit(node)
        node = self.visit_Module(node)
        return node

    def valid_node(self, node: ast.Dict):
        """
        Check that the node information in the diagram conforms to the specification
        """
        if len(node.keys) != len(NODE_DEFINE):
            raise CommandError(f'Run failed, Invalid graph.Each node must have these five properties:{NODE_DEFINE}')

        for idx, key in enumerate(node.keys):
            if key.s != NODE_DEFINE[idx]:
                raise CommandError(
                    f'Run failed, Invalid graph.Each node must have these five properties in order:{NODE_DEFINE}')


class RemoveNodeTransformer(BaseTransformer):
    """
    Remove Node Transformer
    """
    rm_old_clz = True
    old_clz = None

    def __init__(self, node_id):
        self.node_id = node_id

    def visit_Module(self, node: ast.Module) -> Any:
        """
        visit module
        """
        # remove old import?
        _idx_1 = None
        _idx_2 = None
        if self.rm_old_clz:
            for idx_x, x in enumerate(node.body):
                if type(x).__name__ == IMPORT_FROM:
                    for idx_y, y in enumerate(x.names):
                        if y.asname and y.asname == self.old_clz:
                            _idx_2 = idx_y
                            break
                        elif not y.asname and y.name == self.old_clz:
                            _idx_2 = idx_y
                            break
                    if _idx_2 is not None:
                        del x.names[_idx_2]
                        _idx_1 = idx_x if not x.names else None
                        break

            if _idx_1 is not None:
                del node.body[_idx_1]

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """
        visit class def
        """
        clz = 'Main'
        base_clz = 'ViewFlow'
        func_name = 'create_nodes'
        if node.name == clz and node.bases[0].id == base_clz:
            for x in node.body:
                if type(x).__name__ == FUNCTION_DEF and x.name == func_name:
                    for y in x.body:
                        if type(y).__name__ == RETURN:
                            _idx = None
                            _target = None

                            for idx, z in enumerate(y.value.elts):
                                # valid node
                                self.valid_node(z)
                                # remove node
                                if z.values[1].s == self.node_id:
                                    _idx = idx
                                    _target = z
                                    self.old_clz = z.values[0].id
                                    break

                            if _target:
                                # update relative node
                                # the successor node of the precursor node changes to the successor node
                                for k in y.value.elts:
                                    self.valid_node(k)
                                    if type(k.values[2]).__name__ == STR and k.values[2].s == _target.values[1].s:
                                        k.values[2] = _target.values[2]
                                    if k.values[0].id == _target.values[0].id and k.values[1].s != _target.values[1].s:
                                        self.rm_old_clz = False

                            if _idx is not None:
                                del y.value.elts[_idx]
                            break

                    break

        return node

    def handle(self, node):
        """
        Override the parent class handler
        """
        node = self.generic_visit(node)
        node = self.visit_Module(node)
        return node
