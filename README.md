# iCAT-workflow

### Installation
1. Vastly overcomplicated but highly recommended environment setup with conda
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
$ (icat) pip install git+git://github.com/lanery/iCAT-workflow/
```

3. Clone GitHub repo
```
$ (icat) git clone https://github.com/hoogenboom-group/iCAT-workflow
```

### Getting started
1. (Optional) Download sample data (~3GB) to a convenient location (will take several minutes)
```
$ (icat) cd /path/to/data/storage/
$ (icat) svn export https://github.com/hoogenboom-group/iCAT-data.git/trunk/pancreas
```

2. Start `jupyter lab` session
```
$ (icat) cd ./iCAT-workflow/
$ (icat) jupyter lab --no-browser --port 8888
```

