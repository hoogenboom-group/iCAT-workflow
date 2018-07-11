# iCAT-workflow

A full installation guide and walkthrough for the iCAT post-processing workflow.

**Last tested: 28-06-2018**
* Ubuntu 16.04.4 LTS 64-bit Virtual Machine
* 4 cores
* 8GB RAM
* 80GB virtual storage

## Initial Setup

### Clone repository
Clone repository somewhere within home directory.
```
git clone https://github.com/lanery/iCAT-workflow.git
```

### Store sample data
Create new directory and copy over sample data
```
sudo mkdir -p /data/projects/iCAT_demo/
sudo cp -R ./iCAT-workflow/iCAT_sample_data/ /data/projects/iCAT_demo/
```

Change owner and user/group permissions
```
sudo chown -R username:username /data/
sudo chmod -R 755 /data/
```

Directory structure should now resemble
```
data
└──┬ projects
   └──┬ iCAT_demo
      └──┬ iCAT_sample_data
         ├──┬ big_tiles
         │  └─── big_tile-00000x00000.ome.tif
         └──┬ lil_tiles
            ├─── tile-00008x00011.ome.tif
            ├─── tile-00008x00012.ome.tif
            ├─── ...
            ├─── tile-00012x00015.ome.tif
            └─── tile-00012x00016.ome.tif

```

## Install Miniconda (Recommended)
If conda is not already installed, navigate to https://conda.io/miniconda.html and download the 64-bit bash installer. Install via
```
bash ~/Downloads/Miniconda3-latest-Linux-x86_64.sh
```
and follow the prompts.

## Install Render Web Services
Follow the installation guide for render-ws at
https://github.com/saalfeldlab/render/blob/master/docs/src/site/markdown/render-ws.md

You can check the status of mongodb with
```
sudo service mongodb status
```
Hopefully it gives the green light.

After running `deploy/jetty_base/jetty_wrapper.sh start` navigate to http://localhost:8080/render-ws/view/index.html to access the render-ws "homepage". Click on "Render Project Dashboard" to view stack information (which should be empty at the moment).

### Relocate render-ws
First stop jetty
```
./deploy/jetty_base/jetty_wrapper.sh stop
```

Then move render library to /usr/local/
```
sudo mv ./render/ /usr/local/
```
and update the environment variables in `jetty_wrapper.sh` to reflect the change
```
export JETTY_HOME="/usr/local/render/deploy/jetty-distribution-9.4.9.v20180320"
export JETTY_BASE="/usr/local//render/deploy/jetty_base"
export JAVA_HOME="/usr/local/render/deploy/jdk1.8.0_131"
```

Restart jetty with
```
/usr/local/render/deploy/jetty_base/jetty_wrapper.sh start
```

If http://localhost:8080/render-ws/view/index.html is still accessible then everything should be good.

## Install render-python
I have no idea how to use the render-ws library. Luckily, Forrest Collman at the Allen Institute wrote a python api for render-ws that someone who knows nothing about java can use. First create a new virtual environment with a bunch of packages pre-installed.
```
conda create -n iCAT numpy scipy matplotlib pandas scikit-image jupyter ipython tqdm seaborn beautifulsoup4
```

Then activate the new virtual environment and install render-python via
```
source activate iCAT
pip install git+https://github.com/fcollman/render-python.git
```

You can check if `render-python` was successfully installed with
```
python -c 'import renderapi'
```
If no error message is returned then it was succesfully installed. There is a very handy [user guide](http://render-python.readthedocs.io/en/latest/guide/index.html) to get acquainted with the api.

## First render-python project
In short, the fundamental entity in `render-ws` is a "stack". A project can have multiple stacks and each stack can contain multiple z layers with each layer containing multiple image tiles. The organizational structure of each stack, its layers, and its layers' tiles are all stored as metadata in a database accessed via http requests. Or something like that. We will now run a `render-python` script to get a feeling for what working with `render-ws` is like.

#### 1 Create Stacks
In `./iCAT-workflow/render-python_scripts/` open `render_iCAT_demo.py` in a text editor. You will see a bunch of parameter information at the top and then a bunch of `render-python` code commented out. Assuming you are in the `iCAT-workflow` directory, try running the `render_iCAT_demo.py` script
```
python ./render-python_scripts/render_iCAT_demo.py
```

If you refresh the `render-ws` dashboard you should see a table appear with the names of the stacks in the script all in the `LOADING` state. You can view information about each stack by clicking on `View --> Metadata` (or by navigating to e.g. http://localhost:8080/render-ws/v1/owner/lanery/project/iCAT_demo/stack/insulin).

#### 2 Import Image Tile Data

