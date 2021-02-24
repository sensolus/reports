This repo contains sample custom reports generated in Python for the Sensolus application.  Those reported are generated offline and then uploaded to system.

Every report can be run from the command line or as a AWS Lamba function.

# Report overview
## Journey
This report creates an XLS file which contains the journeys for all trackers of the previous day.  For every journey segment the start location, start time, stop location, stop time, distance & duration is given.

# Setting up Pyton environment
The most practical way is to setup a virtual environment for python

```Bash
virtualenv -p python3 ENV
source ./ENV/bin/activate
```

Now install all dependencies:
```
pip install -r requirements.txt
```

# Running a report from the command line
Every report

# How to package as an AWS Lamba
See https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-venv for  instructions on package a Python script with its dependencies.

The instructions are repeated here:

1. Decativate the virtual environment
```Bash
deactivate
```
2. Add the dependent libraries at the root
```Bash
cd ENV/lib/python3.8/site-packages
zip -r ../../../../my-deployment-package.zip .
cd ../../../..
```
Note that your python version might be different.  Update if needed.

3. Add our own scripts to the mix
```Bash
zip -g my-deployment-package.zip reports/*
```
4. Upload the zip throught the lambda web console
