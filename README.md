# PyLab
Python lab equipment scripting library

## Installation
A VISA backend is needed.  Currently development is being done with these items... 
- pyvisa-py: python based VISA implementation
- psutil: to help with TCPIP:instr resource discovery
- zeroconf: to help with TCPIP:hislip resource discovery
The above will be install by default, but different VISA backends can be used if desired.

> ⚠️ **NOTE:** PyLab requires Python 3.13 or greater.  Check your versions!

### Windows
Here is the recomended way, but you can simplify if you prefer.  This assumes that you have a working Python3 installation.

The rest of these instructions assume you have opened a terminal and navigated to your prefered working directory.

1. Clone PyLab
Grab the latest source from GitHub and clone
```
git clone <repo path> .\PyLab
```

2. Create a new virtual environment.
```
python venv venv-pylab
```
This will create a new virtual environment in the ```venv-pylab``` folder. Normally this folder would be called just ```venv``` - you can call it whatever you like.  For systems where you might have more than one virtual environment setup, more descriptive names are nice.

3. Active the new virtual environment.
```
venv-pylab\Scripts\activate.bat
```
After executing this command, your terminal prompt should have an added prefix with your virtual environment name, like the example below.

```
(venv-pylab) user@computer C:\dev
$
```

4. Install PyLab
Change the path to the PyLab directory to match where you have pulled 
```
python -m pip install .\PyLab
```

If you expect to make edits to code while using PyLab, then you probably want to instead install as an editable installation, in which case the ```-e``` argument should be passed as well.

5. Test Installation

Test ability to import PyLab by running python and importing.  You should see something like the below terminal snippet.
```
$ python
Python 3.14.2 (...) [MSC v.1944 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import pylab
>>>
```

PyLab comes with some optional command line scripts.  To test these, make sure you can call pylab directly.

```
$ pylab
usage: pylab [-h] [-t CONN_TYPE] {list,identify,write,read} ...
pylab: error: the following arguments are required: command
```

6. Optional: Install Jupyter
Jupyter gives a nice interface for scripting stuff... but it is not needed.
```
python -m pip install jupyterlab
```

### Linux/WSL
Excel interface is not available but it works.  Will update docs later - ask for help if you want this type of install.  Currently most development is done on a linux install using WSL with a Debian image.
