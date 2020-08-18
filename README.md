# arkfbp-py

arkfbp-py is the python implementation of the arkfbp.

# installation

    pip3 install arkfbp

# Dev installation

    python3 setup.py install
    
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
    from app1.flows.flow1.nodes.node1 import Node1


    class Main(ViewFlow):

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

8、在`demo/arkfbp/routes/demo.json`中配置路由信息:
    
    {
        "namespace": "demo/v1/",
        "routes": [
            {
                "flow1/": {
                    "get": "app1.flows.flow1"
                }
            }
        ]
    }

9、迁移路由信息，其中参数`--topdir`可指定路由配置信息所在目录，参数`--urlfile`可指定迁移后的文件所在路径:

    python3 manage.py migrateroute --topdir demo --urlfile demo/demo_urls.py

10、将`9`中生成的url文件，配置到项目的demo/urls.py中
    
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('demo.demo_urls'))
    ]

11、尝试运行流`flow1`:

    python3 manage.py runflow --flow app1.flows.flow1.main --input example

12、使用`django`原生方式启动`server`
    
    python3 manage.py runserver 0.0.0.0:8000
