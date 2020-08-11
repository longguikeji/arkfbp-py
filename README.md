# arkfbp-py

arkfbp-py is the python implementation of the arkfbp.

# installation

    pip install arkfbp

# Quick Start

1、新建名为`demo`的项目:

    arkfbp-admin startproject demo

2、此时可使用`arkfbp-admin`或者`manage.py`文件进行`app`、`flow`及`node`的创建，注意：若使用`manage.py`，需要将:

        from django.core.management import execute_from_command_line

替换为：

        from arkfbp.common.django.management import execute_from_command_line

3、新建名为`app1`的应用:

    arkfbp-admin startapp app1

4、移动到`demo/app1/flows`目录下，新建名为`flow1`的流:

    arkfbp-admin startflow flow1
 
5、移动到`demo/app1/flows/flow1/nodes`目录下，新建名为`node1`的节点:

    arkfbp-admin startnode node1

6、在`Node1`的`run`方法示例如下:

        def run(self, *args, **kwargs):
            print(f'Hello, Node1!')
            return HttpResponse('hello arkfbp')

7、`demo/app1/flows/flow1`的`main.py`示例如下:
    
    from arkfbp import Graph, StartNode, StopNode

    # Editor your flow here.
    from arkfbp.flow import ViewFlow
    from user.flows.create.nodes.node1 import Node1
    from user.flows.create.nodes.node2 import Node2


    class Main(ViewFlow):

        allow_http_method = ['GET']

        def create_graph(self):
            g = Graph()
            g.nodes = self.create_nodes()
            g.edges = ['']
            return g

        def create_nodes(self):
            return [
                {
                    'cls': StartNode,
                    'id': 'start',
                    'next': 'node1'
                },
                {
                    'cls': Node1,
                    'id': 'node1',
                    'next': 'stop'
                },
                {
                    'cls': StopNode,
                    'id': 'stop'
                }
            ]

8、在`demo/demo/urls`中设置`url`:
    
    from demo.flows.flow1.main import Main as view_flow1

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('demo/', view_flow1.as_view(), name='demo'),
    ]

9、尝试运行流`flow1`:

    python manage.py runflow --flow app1.flows.flow1.main --input example

10、使用`django`原生方式启动`server`
