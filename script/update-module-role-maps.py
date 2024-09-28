import os
import glob
import yaml
import json


# Set the path to ../modules/ relative to the location of the script
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "modules")

# Define the role to slug mapping
role_mapping = {
    "Investigator": "investigator",
    "Research Leaders": "research-leader",
    "Informaticist": "informaticist",
    "Software Engineer": "software-engineer",
    "Clinician Scientist/Trainee": "clinician-scientist"
}

# Define the role module map
role_module_map = []

# Load data from _quarto.yml sidebar
# sidebar = None;
# with open(os.path.join(path, '..', '_quarto.yml'), 'r') as f:
#    quarto_data = yaml.safe_load(f.read().strip());
#    sidebar = quarto_data['website']['sidebar']

# print(str(quarto_data['website']['sidebar'][0]))

# Extract data
# for item in sidebar:
#    if isinstance(item, str): # direct link item
#        pass # save order, extract title from frontmatter
#    elif isinstance(item, dict) and item.has_key?('text'):
#        pass # save order and title
#    elif isinstance(item, dict) and item.has_key?('contents'):
#        pass # recurse
#    else:
#        pass

# Read in the _quarto.yml file
quarto_file = os.path.join(path, "..", "_quarto.yml")
with open(quarto_file, "r") as f:
    try:
        quarto_yaml = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(e)

# Collapse sidebar down to just the filenames so we can get the ordering
a = [menu['contents'] for menu in quarto_yaml['website']['sidebar']]
a = [item for sublist in a for item in sublist] # Flatten - https://stackoverflow.com/questions/952914/
b = [x['contents'] for x in a if type(x) is dict and 'contents' in x]
b = [item for sublist in b for item in sublist] # Flatten - https://stackoverflow.com/questions/952914/
c = [x if type(x) is dict else {'file': x} for x in b]

# Sub-sub levels need to be replaced and collapsed.
d = [x['contents'] if type(x) is dict and 'contents' in x else x for x in c]
# Flatten
e = []
for item in d:
    if isinstance(item, list):
        e.extend(item)
    else:
        e.append(item)

ordering = {x['file'].replace('modules/', '').replace('.qmd', ''): x for x in e}

for pos, k in enumerate(ordering.keys()):
    ordering[k]['position'] = pos


# Loop through each Markdown file in the path
for filename in glob.glob(os.path.join(path, "*.qmd")):
    module_slug = os.path.splitext(os.path.basename(filename))[0]
    if module_slug not in ordering:
        continue
    with open(filename, "r") as f:
        # Read the file content
        content = f.read()

        # Parse the YAML frontmatter
        _, frontmatter, markdown = content.split("---", 2)
        frontmatter = yaml.safe_load(frontmatter.strip())

        # Extract the roles from the frontmatter
        roles = frontmatter.get("roles")

        # If the roles exist, add the filename to the corresponding role in the role module map
        if roles:
            for role in roles:
                role_slug = role_mapping.get(role)
                if role_slug:
                    existing_role = next(
                        (r for r in role_module_map if r["role"] == role_slug),
                        None)
                    text = ordering[module_slug].get('text', frontmatter['title'])
                    if text == "Introduction":
                        text = frontmatter['title']
                    entry = {
                        "slug": module_slug,
                        "position": ordering[module_slug]['position'],
                        "text": text
                    }
                    if not existing_role:
                        role_module_map.append({
                            "role":
                            role_slug,
                            "modules": [entry]
                        })

                    else:
                        existing_role["modules"].append(entry)

# Sort the role module map by role
role_module_map = sorted(role_module_map, key=lambda r: r["role"])

# Sort within roles by position
for m in role_module_map:
    m['modules'] = sorted(m['modules'], key=lambda r: r["position"])

# Convert the role module map to a JavaScript variable
js_var = "const role_module_map = " + json.dumps(role_module_map, indent=2) + ";"

# Write the JavaScript variable to mappings.js
with open(os.path.join(path, "mappings.js"), "w") as f:
    f.write(js_var)
