import ast
from typing import Any

import astunparse
from yapf.yapflib.yapf_api import FormatFile

IMPORT_FROM = 'ImportFrom'
FUNCTION_DEF = 'FunctionDef'
RETURN = 'Return'


class BaseTransformer(ast.NodeTransformer):

    def generic_visit(self, node):
        # has_lineno = getattr(node, "lineno", "None")
        # col_offset = getattr(node, "col_offset", "None")
        # print(type(node).__name__, has_lineno, col_offset)
        super(BaseTransformer, self).generic_visit(node)
        return node

    def execute(self, file):
        """must be overridden"""
        pass


class AddNodeTransformer(BaseTransformer):

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
        # Remove Duplicates
        insert_index = 0
        for index, x in enumerate(node.body):
            if type(x).__name__ == IMPORT_FROM:
                if x.module == self.module:
                    for y in x.names:
                        if y.name == self.clz and y.asname == self.clz_as:
                            return node
            else:
                insert_index = index
                break
        # add a ImportFrom Node
        new_node = ast.ImportFrom(module=self.module, names=[ast.alias(name=self.clz, asname=self.clz_as)], level=0)
        node.body.insert(insert_index, new_node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        clz = 'Main'
        base_clz = 'ViewFlow'
        func_name = 'create_nodes'
        self.clz = self.clz_as if self.clz_as else self.clz
        if node.name == clz and node.bases[0].id == base_clz:
            for x in node.body:
                if type(x).__name__ == FUNCTION_DEF and x.name == func_name:
                    for y in x.body:
                        if type(y).__name__ == RETURN:
                            dict_node = ast.Dict(
                                keys=[ast.Str(s='cls'), ast.Str(s='id'), ast.Str(s='next'), ast.Num(n='x'),
                                      ast.Num(n='y')],
                                values=[ast.Name(id=self.clz, ctx=ast.Load()),
                                        ast.Str(s=self.node_id),
                                        ast.Str(s=self.next_node_id),
                                        ast.Num(n=self.coord_x),
                                        ast.Num(n=self.coord_y),
                                        ])
                            y.value.elts.append(dict_node)
        return node

    def execute(self, file):
        r_node = parse_code(file)
        r_node = self.visit_Module(r_node)
        r_node = self.generic_visit(r_node)
        parse_ast(r_node, file)
        return r_node


def parse_code(file):
    with open(file, 'r') as f:
        node = ast.parse(f.read())
    return node


def parse_ast(node, file):
    code_body = astunparse.unparse(node)
    with open(file, 'w') as f:
        f.write(code_body)
    # reformat a string of code
    FormatFile(file, style_config='pep8', in_place=True)
