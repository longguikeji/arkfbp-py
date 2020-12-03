# 自动化项目开发文档

## 自动化接口生成原理
读取指定的JSON文件夹中的所有配置文件，通过automation.flows.core中的MetaConfigs.get_urls()，
将所有api描述相关的接口实例化为一条条工作流(ViewFlow)。

## 自动化接口运行时
Request -> core -> admin flow -> PermissionCore Node -> SerializerCore Node -> Response

1) HTTP请求到达admin flow的第一个节点PermissionCore，输入为django原生request，此节点从api配置信息中获取权限信息，
并将所有权限校验流实例化并运行，返回结果为Boolean类型。

2) HTTP请求到达admin flow的第二个节点SerializerCore，输入为django原生request，
此节点工作流程分为：初始化serializer node、运行serializer node(数据校验)、运行handle function(CRUD)。

    (1) 初始化master serializer node
    
    从api配置信息中提取request相关参数生成field node，并统一给到动态创建的master serializer node class，之所以称之为master，
    是因为serializer node也可以包含serializer node。
    
    (2) 运行serializer node
    
    通过运行serializer node的run()方法对请求中各参数进行数据校验，不通过的所有字段统一返回错误信息。
    
    (3) 运行handle function
    
    为modeling.AutoModelSerializerNode类独有的handle()方法，通过此方法将系统内置的CRUD操作及自定义操作封装其中，将最终json结果返回。

## 系统内置获取配置接口生成原理
内部通过预先设置好的`meta_config/<meta_name>/`后缀，生成此接口。
生成此接口的位置在core中的MetaConfigs.config_url()中。

## 系统内置获取配置接口运行时

Request -> core -> meta_config flow -> ConfigMeta Node -> Response

1) HTTP请求到达meta_config flow的第一个节点ConfigCore，输入为django原生request，从request中获取meta name参数，
并从配置文件夹中搜索对应的meta config及其依赖，转化为JSON数据返回。
