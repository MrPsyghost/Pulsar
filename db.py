import json
import os

def create(file_path):
    if os.path.exists(file_path):
        with open(file_path,'r') as f:
            data = json.load(f)
    else:
        with open(file_path,'w') as f:
            data={}
            json.dump(data,f,indent=4)
    return data

def save(file_path,data):
    if os.path.exists(file_path):
        with open(file_path,'w') as f:
            json.dump(data,f,indent=4)