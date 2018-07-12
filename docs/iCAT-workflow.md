# iCAT Workflow
A walkthrough for getting started with the iCAT post-processing workflow on the sonic server. This walkthrough assumes that both `render` and `catmaid` are up and running successfully and that either you or someone else has gone through the `iCAT-startup` instructions on your behalf.

## First render-python project
In short, the fundamental entity in `render-ws` is a "stack". A project can have multiple stacks and each stack can contain multiple z layers with each layer containing multiple image tiles. The organizational structure of each stack, its layers, and its layers' tiles are all stored as metadata in a database accessed via http requests. Or something like that. We will now run a `render-python` script to get a feeling for what working with `render-ws` is like.

#### 1 Create Stacks
In `./iCAT-workflow/render-python_scripts/` open `render_iCAT_demo.py` in a text editor. You will see a bunch of parameter information at the top and then a bunch of `render-python` code commented out. Assuming you are in the `iCAT-workflow` directory, try running the `render_iCAT_demo.py` script
```
python ./render-python_scripts/render_iCAT_demo.py
```

If you refresh the `render-ws` dashboard you should see a table appear with the names of the stacks in the script all in the `LOADING` state. You can view information about each stack by clicking on `View --> Metadata` (or by navigating to e.g. http://localhost:8080/render-ws/v1/owner/lanery/project/iCAT_demo/stack/insulin).

#### 2 Import Image Tile Data

