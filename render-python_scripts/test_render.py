import renderapi
from renderapi.layout import Layout
from renderapi.transform import AffineModel
from renderapi.tilespec import TileSpec


# Create a renderapi.connect.Render object
render_connect_params = {
    'host': 'localhost',
    'port': 8080,
    'owner': 'jon_snow',
    'project': 'winterfell',
    'client_scripts': \
        '/usr/local/render/render-ws-java-client/src/main/scripts',
    'memGB': '2G'
}

render = renderapi.connect(**render_connect_params)

# Make a new stack
stack = 'winter_stack'
renderapi.stack.create_stack(stack,render=render)

# Define a tile layout
layout = Layout(sectionId='1',
                scopeId='longclaw_scope',
                cameraId='ghost_cam',
                imageRow=0,
                imageCol=0,
                stageX=100.0,
                stageY=300.0,
                rotation=0.0,
                pixelsize=3.0)

# Define a simple transformation, here a translation based upon layout
at = AffineModel(B0=layout.stageX/layout.pixelsize,
                 B1=layout.stageY/layout.pixelsize)

# Define a tile
tilespec = TileSpec(tileId='000000000000',
                    z=0.0,
                    width=2048,
                    height=2048,
                    imageUrl='file:/opt/tiles/pancrea2/pancrea9-0x0.tif',
                    maskUrl=None,
                    layout=layout,
                    tforms=[at])

# Use the simple non-parallelized upload option
renderapi.client.import_tilespecs(stack,
                                  [tilespec],
                                  render=render)

# Now close the stack
renderapi.stack.set_stack_state(stack, 'COMPLETE', render=render)

