# iCAT Startup
Generic startup instructions for getting a new user up and running on the sonic server with further instructions for installing miniconda and `render-python` as the preface for the `iCAT-workflow`.

## Add New User
#### Note: Must have root access
#### Create new user
```
adduser <username>
passwd <username>
```
#### Add user to samba
```
smbpasswd -a <username>
```
#### Give new user directories in short and long term storage
```
mkdir /short_term_storage/<username>
chown <username>:<username> /short_term_storage/<username>
mkdir /long_term_storage/<username>
chown <username>:<username> /long_term_storage/<username>
```
#### Make CATMAID directory in `/long_term_storage/`
```
mkdir -p /long_term_storage/<username>/CATMAID/projects
```


## Install Miniconda
Navigate to home directory and download the miniconda installation shell script
```
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh

bash ~/miniconda.sh -b -p ~/miniconda
```

This may or may not successfully prepend `~/miniconda/bin` to your path. To test, start a new shell and enter `which python`. If the prompt returns `~/miniconda/bin/python` you are good to go. If not add the line
```bash
export PATH="/home/rlane/miniconda/bin:$PATH"
```
to the end of your `~/.bash_profile`.

You can then remove the install file with
```
rm ~/miniconda.sh
```


## Install render-python
I have no idea how to use the render-ws library. Luckily, Forrest Collman at the Allen Institute wrote a python api for render-ws that someone who knows nothing about java can use. First create a new virtual environment (named `icat`) with a bunch of packages pre-installed. Some of these are required and/or recommended for `render-python`, others are just convenient.
```
conda create -n icat <packages>
```
Packages: `numpy scipy cython matplotlib pandas scikit-image jupyter ipython tqdm seaborn beautifulsoup4 lxml`

Then activate the new virtual environment and install `render-python` via
```
source activate icat
pip install git+https://github.com/fcollman/render-python.git
```

You can check if `render-python` was successfully installed with
```
python -c 'import renderapi'
```
If no error message is returned then it was succesfully installed. There is a very handy [user guide](https://render-python.readthedocs.io/en/latest/guide/index.html) to get acquainted with the api.


## Start iCAT Workflow
The startup procedure is now complete. You should now be ready to get started with the [iCAT workflow](https://github.com/lanery/iCAT-workflow/blob/master/docs/iCAT-workflow.md).
