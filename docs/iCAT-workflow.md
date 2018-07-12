# iCAT Workflow
A walkthrough for getting started with the iCAT post-processing workflow on the sonic server. This walkthrough assumes that both `render-ws` and CATMAID are up and running successfully and that you have gone through the [`iCAT-startup`](https://github.com/lanery/iCAT-workflow/blob/master/docs/iCAT-startup.md) guide (or that someone else has on your behalf).

First, check that both `render-ws` and CATMAID are running.
```
systemctl status render
systemctl status catmaid
```
And if you get the green light, go to the homepages for `render-ws` and CATMAID

| Service           | Homepage                                      |
| ----------------- | --------------------------------------------- |
| `render-ws` views | http://sonic:8080/render-ws/view/index.html   |
| CATMAID           | http://sonic/catmaid/                         |

Also make sure that the `icat` conda environment is the active environment.


## Clone this repository
This repository contains sample data and scripts helpful for running through an introductory iCAT workflow/project. Assuming you are somewhere in your home directory
```
git clone https://github.com/lanery/iCAT-workflow.git
```

#### Sample Data
The sample data is organized such that each "stack" of images is stored in its own directory. A "stack" is a key concept within the `render-ws` + CATMAID ecosystem that will be expanded upon later. But basically, a stack can be thought of a collection of **one or more** *images* at **one or more** *layers in z* from **one** *imaging channel*. Hence, all of the small EM tiles will belong to one stack as will the large EM tiles, as will each fluorescence channel. It is perhaps easiest to grasp this organization scheme by looking at the directory tree of the sample data (`iCAT-workflow/iCAT_sample_data`)
```
iCAT-workflow
└───┬ iCAT_sample_data
    ├───┬ amylase
    │   └─── amylase-00000x00000.ome.tif
    ├───┬ big_EM
    │   └──── big_EM-00000x00000.ome.tif
    ├───┬ hoechst
    │   └──── hoechst-00000x00000.ome.tif
    ├───┬ insulin
    │   └──── insulin-00000x00000.ome.tif
    └───┬ lil_EM
        ├──── lil_EM-00008x00011.ome.tif
        ├──── lil_EM-00008x00012.ome.tif
        ├──── ...
        ├──── lil_EM-00012x00015.ome.tif
        └──── lil_EM-00012x00016.ome.tif

```
This is (at least for now) the optimal organization scheme for working with image data in the workflow. Unfortunately, it is not how raw data is output by Odemis. How to go from raw Odemis data to nicely organized, iCAT-friendly data will be covered later.

It is assumed that if you are going to be viewing your data in CATMAID, then it is worthy of long term storage. Even though this is just sample data, we will treat it as if it were a real project. Thus, copy the sample data to your long term storage folder.
```
cd ./iCAT-workflow/
cp -a ./iCAT_sample_data/ /long_term_storage/<user>/<data storage folder>/
```


## First render-python project
A project can have multiple stacks and each stack can contain multiple z layers with each layer containing multiple image tiles. The organizational structure of each stack, its layers, and its layers' tiles are all stored as metadata in a database accessed via http requests. Or something like that. We will now run a `render-python` script to get a feeling for what working with `render-ws` is like.

#### 1 Create Stacks
In `./iCAT-workflow/render-python_scripts/` open `render_iCAT_demo.py` in a text editor. You will see a bunch of parameter information at the top and then a bunch of `render-python` code commented out. On the line
```python
'owner': '<owner>'
```
change `<owner>` to your username. Then, assuming you are in the `iCAT-workflow` directory, try running the script.
```
python ./render-python_scripts/render_iCAT_demo.py
```

Now, on the `render-ws` view page, go to the `Render Project Dashboard`. You should see a table with the names of the stacks in the script all in the `LOADING` state. You can view information about each stack by clicking on `View --> Metadata` (or by going to `http://sonic:8080/render-ws/v1/owner/<user>/project/iCAT_demo/stack/<stack>`).

#### 2 Import Image Tile Data

