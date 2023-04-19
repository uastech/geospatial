from ruamel.yaml import YAML

yaml = YAML()
with open('../geospatial.yaml', 'r') as f:
    api = yaml.load(f)

with open('../geospatial.yaml', 'w') as f:
    yaml.dump(api, f)
