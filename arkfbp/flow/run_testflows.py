import os,sys
from arkfbp.flow import executer
import importlib
#from app1.flows.testtest.main import Main

def run_testFlows():
    file_dir = './app1/flows/'
    for file in os.listdir(file_dir):
        path = os.path.join(file_dir, file)
        if os.path.isdir(path) and file.startswith('testt'):
            if 'main.py' in os.listdir(path):
                print(file+'--------------------------------------------')
                try:
                    a = importlib.import_module("app1.flows." +file+ ".main") 
                    main = a.Main()
                    sys.stdout.write(executer.FlowExecuter.start_test_flow(main, inputs={}, http_method='get') + '\n')
                except Exception as e:
                    sys.stdout.write(str(e))