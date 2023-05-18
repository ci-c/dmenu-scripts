#!/usr/bin/python3

import jstyleson
import subprocess
import sys
import pathlib

class VarList:
    def __init__(self):
        self.vars:dict[str:any] = {}
    def __getitem__(self, key:str):
        try: return self.vars[key].format(**self.vars)
        except KeyError: return None
    def __setitem__(self, key:str, value:any):
        self.vars[key] = value
    def __delitem__(self, key:str):
        self.vars.remove(key)
    

class Command:
    def __init__(self, obj:dict[str:list[str]|None|str], vars:VarList):
        self.command:list[str] = obj["coommand"]
        self.stdin:str|None = obj["stdin"]
        self.stdout:str|None = obj["stdout"]
        self.vars:VarList = vars
    def run(self):
        command = []
        for item in self.command:
            command.append(item.format(**self.vars.vars))
        out = subprocess.run(command,input=self.vars[self.stdin],stdout=subprocess.PIPE)
        if self.stdout is not None:
            self.vars[self.stdout] = out.stdout
        if out.returncode != 0:
            print(out.stderr.decode("utf-8"))

            

class Item:
    def __init__(self, obj:dict[str:str|list[dict[str:list[str]|None|str]]|dict[str:list[str]|None|str]], vars:VarList, config:dict[str:any]):
        self.vars:VarList = vars
        self.format:str =obj["format"]
        self.commandsFormat:list[Command] = []
        for item in obj["commands-format"]:
            self.commandsFormat.append(Command(item, self.vars))
        self.command:Command|None = Command(obj["command"], self.vars) if obj["command"] is not None else None
        self.script:pathlib.Path|None = pathlib.Path(obj["script"]) if obj["script"] is not None else None
        self.is_generator: bool = obj["is-generator"]
    def getText(self):
        for cmd in self.commandsFormat:
            cmd.run()
        if self.is_generator:
            print("TODO")
            return self.format.format(**self.vars.vars)
        else:
            return self.format.format(**self.vars.vars)
    def onSelect(self):
        if self.command is not None: self.command.run() 
        if self.script is not None: Script(self.script, config, self.vars).run()

class Script:
    def __init__(self, filename:pathlib.Path, config:dict[str:any], vars:VarList):
        data:dict = {}
        self.textList:list[str] = []
        self.vars:VarList = vars
        with open(filename, "r") as file:
            data:dict = jstyleson.load(file)
        self.menu_args:list[str] = ["bemenu"] + data["menu-args"] + config["menu-args"]
        self.list:list[Item] = []
        for item in data["list"]:
            self.list.append(Item(item, self.vars, config))
            
    def generateTextList(self):
        for item in self.list:
            if item.is_generator:
                pass
            else:
                self.textList.append(item.getText())
    
    def  selectItem(self, itemName:str):
        for id, item in enumerate(self.textList):
            customInput:bool = True
            if itemName[:-1] == item:
                self.list[id].onSelect()
                customInput = False
                break
    def run(self):
        self.generateTextList()
        out = subprocess.run(self.menu_args, input="\n".join(self.textList).encode("utf-8"), stdout=subprocess.PIPE)
        if out.returncode != 0:
            print(out.stderr.decode("utf-8"))
        if out.stdout.decode("utf-8") is not None:
            self.selectItem(itemName=out.stdout.decode("utf-8"))

def main():
    script = Script(filename="examples/test.jsonc",config={"menu-args":[]}, vars=VarList())
    script.run()

if __name__ == '__main__':
    main()