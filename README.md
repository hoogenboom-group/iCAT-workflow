# iCAT-workflow
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

### Relocate sample data
Create new directory and move over sample data
```
sudo mkdir -p /data/projects/iCAT_demo/
sudo mv ./iCAT-workflow/iCAT_sample_data/ /data/projects/iCAT_demo/
```

Change owner and user/group permissions
```
sudo chown -R username:username /data/
sudo chmod -R 755 /data/
```

<!-- Optionally remove Thumbs.db files
```
rm /data/projects/iCAT_demo/iCAT_sample_data/Thumbs.db
rm /data/projects/iCAT_demo/iCAT_sample_data/lil_tiles/Thumbs.db
```
 -->
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

## Relocate render-ws
```
./deploy/jetty_base/jetty_wrapper.sh stop
```
