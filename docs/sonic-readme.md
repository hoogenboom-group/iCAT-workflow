# Sonic Configuration

## To Run Jupyter Notebook
#### On sonic
```
<user>@sonic $ jupyter notebook --no-browser --port=8889
```
#### On local machine
```
<user>@TUD278418 > ssh -N -L localhost:8888:localhost:8889 <user>@sonic
```
Go to http://localhost:8888/ and copy and paste token from sonic
