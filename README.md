# arkfbp-py

arkfbp-py is the python implementation of the arkfbp.

# installation

    pip3 install arkfbp
    
    or
    
    pip3 install git+https://github.com/longguikeji/arkfbp-py.git@zzr/basic
    
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
    
    from arkfbp.node import StartNode, StopNode
    from arkfbp.graph import Graph
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

    python3 manage.py runflow --flow app1.flows.flow1.main --input {\"username\": \"admin\"} --http_method post --header {\"Authorization\": \"token\"}

12、使用`django`原生方式启动`server`
    
    python3 manage.py runserver 0.0.0.0:8000

# Advanced usage

## Global Hook Flow

全局钩子式工作流运行的场景适用于：

1）服务进行路由之前（self.before_route）

2）所有工作流运行之前（self.before_flow）

3）所有工作流运行之后（self.after_flow）

4）抛出异常之前（self.before_exception）

### 简单使用

1、创建全局钩子式工作流，在项目根目录创建`hook.py`文件(仅为示例)

    from arkfbp.flow import GlobalHookFlow
    class HookFlow(GlobalHookFlow):
    
        def create_nodes(self):
            return [
                {
                    'cls': StartNode,
                    'id': 'start',
                    'next': 'stop'
                },
                {
                    'cls': StopNode,
                    'id': 'stop'
                }
            ]
    
        def set_mount(self):
            self.before_flow = True

2、在`set_mount()`方法中设置想要开启钩子的位置
    
    def set_mount(self):
        """
        设置为在所有工作流运行之前执行全局钩子流
        """
        self.before_flow = True

3、将钩子流配置到项目的`settings.py`文件的`MIDDLEWARE`变量中

    INSTALLED_APPS = [
        ...
    ]
    MIDDLEWARE = [
        ...
        'hook.HookFlow'
    ]

## Flow Hook

1、流创建成功后

    def created(inputs, *args, **kwargs):
        pass

2、流初始化之前

    def before_initialize(inputs, *args, **kwargs):
        pass
            
3、流初始化之后

    def initialized(inputs, *args, **kwargs):
        pass
    
4、流执行之前

    def before_execute(inputs, *args, **kwargs):
        pass
        
5、流执行之后

    def executed(inputs, ret, *args, **kwargs):
        pass
 
6、流被销毁之前

    def before_destroy(inputs, ret, *args, **kwargs):
        pass

## ShutDown Flow

现在，你可以通过`flow.shutdown(outputs, **kwargs)`方法，来随时随地的停止工作流的运行

如果你使用`ViewFlow`来定义流，那么可指定返回的`response`的状态码`response_status`，例如：

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
        
        def before_initialize(inputs, *args, **kwargs):
            self.shutdown('Flow Error！', response_status=400)


## Flow State


## Flow Steps

`flow.steps`为一个`dict`，其中包含以`node_id`为`key`、以`node_instance`为`value`的数据

现在你可以在任何一个节点，从`node.state.steps`中，获取指定的已运行的`node`

    node1 = node.state.steps.get('node1', None)
