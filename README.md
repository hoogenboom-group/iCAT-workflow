# iCAT-workflow
Post-processing workflow for volume CLEM image data.

### Installation
Assumes you are logged into a remote Linux server with [conda](https://docs.conda.io/en/latest/miniconda.html#linux-installers) configured.

1. Vastly overcomplicated but highly recommended environment setup with conda.
```
$ conda create -n icat jupyterlab altair vega_datasets
$ conda activate icat
$ (icat) conda install -c conda-forge nodejs=15
$ (icat) pip install tqdm lxml ipympl ipywidgets imagecodecs ruamel.yaml
$ (icat) pip install git+git://github.com/AllenInstitute/BigFeta/
$ (icat) jupyter labextension install @jupyter-widgets/jupyterlab-manager
$ (icat) jupyter labextension install jupyter-matplotlib
$ (icat) jupyter nbextension enable --py widgetsnbextension
```

2. Install iCAT-workflow from github repo
```
$ (icat) pip install git+https://github.com/hoogenboom-group/iCAT-workflow.git
```

3. Clone GitHub repo
```
$ (icat) git clone https://github.com/hoogenboom-group/iCAT-workflow
```

### Getting started

1. Connect to remote server with port forwarding e.g.
```
ssh -L 8888:localhost:8888 {user}@{server}
```

2. (Optional) Download sample data (~3GB) to a convenient location (will take several minutes)
```
$ (icat) cd /path/to/data/storage/
$ (icat) svn export https://github.com/hoogenboom-group/iCAT-data.git/trunk/pancreas
```

3. Start `jupyter lab` session
```
$ (icat) cd ./iCAT-workflow/
$ (icat) jupyter lab --no-browser --port 8888
```

4. Open a browser and navigate to http://localhost:8888/lab to run jupyter lab session
