# iCAT-workflow

### Installation
1. Vastly overcomplicated but highly recommended environment setup with conda
```
$ conda create -n icat jupyterlab shapely
$ conda activate icat
$ (icat) conda install -c conda-forge nodejs=15
$ (icat) pip install tqdm lxml ipympl ipywidgets
$ (icat) jupyter labextension install @jupyter-widgets/jupyterlab-manager
$ (icat) jupyter labextension install jupyter-matplotlib
$ (icat) jupyter nbextension enable --py widgetsnbextension
```

2. Install iCAT-workflow from github repo
```
$ (icat) pip install git+git://github.com/lanery/iCAT-workflow/
```
