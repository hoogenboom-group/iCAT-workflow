# -*- coding: utf-8 -*-
"""
@Author: rlane
@Date:   27-05-2018 14:57:10
"""

import subprocess
from pathlib import Path
import renderapi


# Render Parameters
project = 'pancrea'
# stack = 'lil_EM_grid'
# match_collection = 'EM_matches'

# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'localhost',
    'port': 8080,
    'owner': 'lanery',
    'project': f'{project}',
    'client_scripts': \
        '/usr/local/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}
render = renderapi.connect(**render_connect_params)

catmaid_export_params = {
    'stack': 'lil_EM_montaged',
    'rootDirectory': '/opt/tiles/big_kahuna/4CATMAID',
    'height': 1024,
    'width': 1024,
    'format': 'jpg',
    'maxLevel': 6,
    'owner': render_connect_params['owner'],
    'project': render_connect_params['project'],
    'baseDataUrl': 'http://localhost:8080/render-ws/v1',
}

subprocess.run([f"{render_connect_params['client_scripts']}/render_catmaid_boxes.sh",
                f"--stack {catmaid_export_params['stack']}",
                f"--rootDirectory {catmaid_export_params['rootDirectory']}",
                f"--height {catmaid_export_params['height']}",
                f"--width {catmaid_export_params['width']}",
                f"--format {catmaid_export_params['format']}",
                f"--maxLevel {catmaid_export_params['maxLevel']}",
                f"--owner {catmaid_export_params['owner']}",
                f"--project {catmaid_export_params['project']}",
                f"--baseDataUrl {catmaid_export_params['baseDataUrl']}",
                f"0"])
