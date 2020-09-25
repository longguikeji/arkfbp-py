# arkfbp-py

arkfbp-py is the python implementation of the arkfbp.

# installation

arkfbp-py需要 Python 3.6+ 及Django 2.0+ 的版本支持。

    pip3 install arkfbp (暂不可用)
    
    or
    
    pip3 install git+https://github.com/longguikeji/arkfbp-py.git@zzr/basic

# Dev installation

    python3 setup.py install
    
# Quick Start

1、新建名为`demo`的项目:

    arkfbp-py startproject demo

2、在项目根目录下，新建名为`app1`的应用:

    arkfbp-py startapp app1

3、移动到`demo/app1/flows`目录下，新建名为`flow1`的流，并设置类型 --class:

    arkfbp-py createflow flow1 --class view
 
4、移动到`demo/app1/flows/flow1/nodes`目录下，新建名为`node1`的节点,并设置类型 --class和标识 --id:

    arkfbp-py createnode node1 --class function --id node1

5、在`Node1`的`run`方法示例如下:

        def run(self, *args, **kwargs):
            print(f'Hello, Node1!')
            return 'hello arkfbp'

6、`demo/app1/flows/flow1`的`main.py`示例如下:
    
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

7、在`demo/arkfbp/routes/demo.json`中配置路由信息:
    
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

8、迁移路由信息，其中参数`--topdir`可指定路由配置信息所在目录，参数`--urlfile`可指定迁移后的文件所在路径，默认会在项目settings.py文件所在路径查找并生成文件:

    python3 manage.py migrateroute --topdir demo --urlfile demo/demo_urls.py

9、将`8`中生成的url文件，配置到项目的demo/urls.py中。
    
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('demo.demo_urls'))
    ]

10、尝试运行流`flow1`:

    python3 manage.py runflow --flow app1.flows.flow1.main --input {\"username\": \"admin\"} --http_method post --header {\"Authorization\": \"token\"}

11、使用`django`原生方式启动`server`。
    
    python3 manage.py runserver 0.0.0.0:8000

# Advanced usage

## GlobalHookFlow（已废弃）

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

2、在`set_mount()`方法中设置想要开启钩子的位置。
    
    def set_mount(self):
        """
        设置为在所有工作流运行之前执行全局钩子流
        """
        self.before_flow = True

3、将钩子流配置到项目的`settings.py`文件的`MIDDLEWARE`变量中。

    INSTALLED_APPS = [
        ...
    ]
    MIDDLEWARE = [
        ...
        'hook.HookFlow',
        'hook.HookFlow1',
        'hook.HookFlow2',
    ]

### HookFlow的执行顺序

`GlobalHookFlow`的执行顺序与`django`原生`Middleware`执行顺序一致，
before_route()、before_flow()的执行顺序依次为从上至下；after_flow()、before_exception()则为从下至上。

## New GlobalHookFlow

全新的钩子流现已可以使用。

### 简单使用

1、在demo/hook/文件夹下创建一个全局钩子流，并设置类型 --class。

    arkfbp-py createflow hook1 --class view

2、创建节点Node1（过程略），并编辑。
    
    class Node1(FunctionNode):

    id = 'node1'

    def run(self, *args, **kwargs):
        print(f'Hello, Hook!')
        return None

3、在demo/arkfbp/hooks/hook.json中设置流的执行位置。
    
    {
        "before_route": ["hook.hook1"],
        "before_flow": [],
        "before_exception": [],
        "before_response": []
    }
4、这样在每次路由之前，都会先进入hook1这个流进行处理。

### 详解

全局钩子式工作流运行的场景适用于：

1）接口路由之前（before_route）

2）工作流运行之前（before_flow）

3）返回响应之前（before_response）

4）抛出异常之前（before_exception）

列表中流的摆放顺序，即为执行顺序。

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

### Flow Shutdown
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

### Node Shutdown
同样，你也可以通过`node.flow.shutdown(outputs, **kwargs)`方法，来随时随地的停止工作流的运行。

如果你使用`ViewFlow`来定义流，那么可指定返回的`response`的状态码`response_status`，例如：
    
    class Node1(FunctionNode):

    id = 'node1'

    def run(self, *args, **kwargs):
        print(f'Hello, Hook 1!')
        self.flow.shutdown('Flow Error！', response_status=400)

## Flow State


## Flow Steps

`flow.steps`为一个`dict`，其中包含以`node_id`为`key`、以`node_instance`为`value`的数据。

现在你可以在任何一个节点，从`node.state.steps`中，获取指定的已运行的`node`。

    node1 = node.state.steps.get('node1', None)

## ViewFlow inputs

`ViewFlow`的`inputs`为原生的`django`的`WSGIRequest`对象，`ViewFlow`在此基础上为`inputs`对象增加了`data`、`extra_data`、`str`属性。

### DataSet

`ds`属性将原生`WSGIRequest`对象的`GET`和`POST`的数据合并为一个`dict`。

### extra_ds

你可以在`extra_ds`中存放你想要传递下去的任何数据。

### str

`str`包含了请求体中的字符串信息。

_注意：你可以随意为inputs增加任何属性，例如：_
    
    inputs.attr = {}

_这样你就为`inputs`增加了`attr`的属性_


## Feature For CLI

### Create Flow

现在你可以通过指定目录和基类来创建一个工作流，`--topdir`参数代表创建流的所在目录，`--class`参数代表工作流期望继承的基类流。

    python3 manage.py createflow flow1 --topdir demo/flows --class base
    
    或者
    
    arkfbp-py createflow flow1 --topdir demo/flows --class base 

详解：--class 参数可选值如下

    {
        'base': 'Flow',
        'view': 'ViewFlow',
        'hook': 'GlobalHookFlow',
    }
    
也可通过命令行获取相关信息

    arkfbp-py createflow -h

### Create Node

现在你可以通过指定目录和基类来创建一个流节点，`--topdir`参数代表创建节点的所在目录，`--class`参数代表节点期望继承的基类节点, `--id`参数代表节点在流中的唯一标识。

    python3 manage.py createnode node1 --topdir demo/flows/flow1/nodes --class base --id node1
    
    或者
    
    arkfbp-py createnode node1 --topdir demo/flows/flow1/nodes --class base --id node1

详解：--class 参数可选值如下

    {
        'base': 'Node',
        'start': 'StartNode',
        'stop': 'StopNode',
        'function': 'FunctionNode',
        'if': 'IFNode',
        'loop': 'LoopNode',
        'nop': 'NopNode',
        'api': 'APINode',
        'test': 'TestNode',
        'trigger_flow': 'TriggerFlowNode',
    }

也可通过命令行获取相关信息

    arkfbp-py createnode -h


## TestFlow

### Create Flow     

1、 通过`Quick Start`中的第3步新建一个工作流，新建的工作流的名称必须以`test`开头。 
2、 将该工作流`main.py`模块里`Main`函数的父类`ViewFlow`修改为`Flow`。  
3、 将`from arkfbp.flow import ViewFlow`修改为`from arkfbp.flow import Flow`。  
这样就得到一个测试流     
测试流的`main.py`如下：         

    from arkfbp.flow import Flow
    from arkfbp.node import StartNode, StopNode
    from app1.flows.testt1.nodes.node1 import Node1

    # Editor your flow here.
    class Main(Flow):

        def create_nodes(self):
            return [
                {
                    'cls': StartNode,
                    'id': 'start',
                    'next': 'node1'
                },{
                    'cls': Node1,
                    'id': 'node1',
                    'next': 'stop'
                },{
                    'cls': StopNode,
                    'id': 'stop'
                }
            ]     
### Create node

1、 通过`Quick Start`中的第4步新建一个节点。 
2、 将新建节点对应`python`文件里节点类的父类`FunctionNode`改为`TestNode`。   
3、 新建节点对应`python`文件里`from arkfbp.node import FunctionNode`修改为`from arkfbp.node import TestNode`。    
这样就得到一个测试节点     
测试节点`node1`如下：

    from arkfbp.node import TestNode

    # Editor your node here.
    class Node1(TestNode):

        def run(self, *args, **kwargs):
            print(f'Hello, Node1!')

### 测试节点使用      

1、 `setUp`函数    
测试节点的`setUp`函数将在测试用例执行之前调用，可用于准备数据等。      

    def setUp(self):
        print('before start test')

2、 `tearDown`函数    
测试节点的`tearDown`函数在测试用例全部执行之后调用。    

    def tearDown(self):
        print('after finish test')

3、 测试用例    
测试用例为以`test_`开头的函数。    

    def test_one(self):
        pass

4、 断言   
测试节点支持`python`自带断言和`django unittest`的断言方法。    

    def test_one(self):
        assert 1==1
    def test_two(self):
        self.assertEqual(1,1)   

5、 调用其他测试流   
在一个测试用例中可以调用其他测试流，得到被调用测试流的结果。调用方式如下：    

    from arkfbp.node import TestNode
    from app1.flows.testt1.main import Main

    class Node1(TestNode):

        def test_other_testflow(self):
            self.get_outputs(Main(),inputs={},http_method='get')

首先需要先从被调用测试流的`main`模块中引入`Main`类，然后调用函数`get_outputs`。       
函数`get_outputs`有三个参数，第一个参数为被调用测试流`Main`类的实例，即`Main()`；第二个参数为输入的数据，字典类型；第三个参数为调用测试流的方法，为`get`     

### Run Flow   

#### 运行指定测试流  

运行指定测试流需要通过调用函数实现。     
1、 在项目目录下新建`python` 文件       
2、 引入`executer`模块     
3、 引入被运行测试流的`Main`类，调用函数`start_test_flow`运行测试流       
函数`start_test_flow`有三个参数，第一个参数为被调用测试流`Main`类的实例，即`Main()`；第二个参数为输入的数据，字典类型；第三个参数为调用测试流的方法，为`get`。运行指定工作流如下：      

    from arkfbp.flow import executer
    from app1.flows.testtest.main import Main

    print(executer.FlowExecuter.start_test_flow(Main(),inputs={},http_method='get'))

#### 运行指定目录下测试流     

1、 在项目目录下新建`python` 文件       
2、 引入`executer`模块     
3、 调用函数`start_all_test_flows`运行测试流        
函数`start_all_test_flows`有一个参数，表示指定的目录，传入相对路径、绝对路径均可。运行指定工作流如下：        

    from arkfbp.flow import executer

    print(executer.FlowExecuter.start_all_test_flows('./app1/flows/'))

若想运行全部测试流也可通过命令实现。在`manage.py`文件所在目录下输入命令`python3 manage.py flowtest`，即可直接运行所有测试流  

## Extension CLI

此部分内容适用于可视化插件开发相关人员

### AddNode

将一个已知的节点信息同步到流的图定义（create_nodes）中

    python3 manage.py ext_addnode --flow <flow_name> --class <node_class> --next <next_node_id> --alias <node_alias> --x <coord_x> --y <coord_y>

#### 示例

    python3 manage.py ext_addnode --flow demo.app1.flows.flow1 --class demo.app1.flows.flow1.nodes.node1.Node1 --next node2 --alias Flow1_Node1 --x 123.123456 --y 123.123456

如果使用`arkfbp-py`命令，需指定`--topdir`参数，其代表项目的绝对根路径：
    
    arkfbp-py ext_addnode --flow demo.app1.flows.flow1 --class demo.app1.flows.flow1.nodes.node1.Node1 --next node2 --alias Flow1_Node1 --x 123.123456 --y 123.123456 --topdir /Users/user/Development/demo

#### 详解

参数`flow`代表流的路径以`.`分隔，具体到流的文件夹名称；参数`class`代表相关节点的路径以`.`分隔，具体到类名；参数`next`代表后继节点的`id`；参数`alias`代表在`import`时，指定的节点类的别名；参数`x`代表插件中的`x`坐标参数；参数`y`代表插件中的`y`坐标参数。
参数`flow`和`class`是必选，其他可选。你也可通过命令行获取相关信息：

    arkfbp-py ext_addnode -h
