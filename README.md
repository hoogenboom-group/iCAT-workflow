# iCAT-workflow
**Last tested: 28-06-2018**
* Ubuntu 16.04.4 LTS 64-bit Virtual Machine
* 4 cores
* 8GB RAM

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
sudo chown -R rlane:rlane /data/
sudo chmod -R 755 /data/
```

Optionally remove Thumbs.db files
```
rm /data/projects/iCAT_demo/iCAT_sample_data/Thumbs.db
rm /data/projects/iCAT_demo/iCAT_sample_data/lil_tiles/Thumbs.db
```

Directory structure should now resemble
```
data
|
└
```

## Install Render Web Services
https://github.com/saalfeldlab/render/blob/master/docs/src/site/markdown/render-ws.md
