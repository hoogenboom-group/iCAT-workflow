# Dynamic Rendering
CATMAID supports dynamic rendering of `render-ws` project stacks meaning a user can quickly and seamlessly view image stacks loaded in `render-ws` without first having to export image to disk. Dynamic rendering is really only suitable as a staging area during alignments. Once your data is nicely aligned, the data still must be tiled and saved to disk.

From Eric Trautman at Janelia:
> At Janelia, we use the dynamic rendering integration while refining alignments and then “materialize” final alignments to disk for tracing. The key caveat is that although dynamic rendering works, it can be slow – particularly when viewing zoomed-out views of thousands of tiles. We work around this limitation by rendering just the bounding boxes of tiles in zoomed-out views and only render tile content once you have zoomed-in to a smaller area.

## How-to
Connect to a machine that has Docker other than the machine running `render-ws`. Create the following Dockerfile and save it as `Dockerfile` (no extension) in a convenient location.
```Dockerfile
FROM trautmane/catmaid:aaa_dev_render_deploy

RUN sed -i 's/renderer.int.janelia.org:8080/sonic:8080/' /home/django/projects/mysite/settings_base.py
```

Build the image from the directory you have just created the Dockerfile in. We will tag it with `tudelft`.
```
$ docker build -t catmaid-render:tudelft ~/path/to/Dockerfile
```

Run a container based on the newly created image
```
$ docker run -it -p 8000:80 --rm catmaid-render:tudelft standalone
```
