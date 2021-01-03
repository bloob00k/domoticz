import json
import os.path

import reloader

class ScriptState(dict):

    def __init__(self, script_name):
        
        self.data = {}
        
        self.state_dir = os.getcwd() + '/_script_data/'
        self.state_file = '__data_' + script_name + '.json'

        self.state_path = self.state_dir + self.state_file
        
        if os.path.exists(self.state_path):
            with open(self.state_path, "r") as ifile:
                self.data = json.load(ifile)

#        self.__dict__ = json.loads(j)

    def __del__(self):
        self.save()
        
    def save(self):
        if not os.path.isdir(self.state_dir):
            os.mkdir(self.state_dir)

        with open(self.state_path, "w") as ofile:
            json.dump(self.data, ofile)


    @staticmethod
    def auto_reload():
        reloader.auto_reload(__name__)
        return
