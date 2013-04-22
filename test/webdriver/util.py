import yaml

def read_conf(env_name):
    conf = None
    with open('config.yaml','r') as f:
        conf = yaml.load(f)
    return conf

