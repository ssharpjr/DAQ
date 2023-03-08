## SETUP

## REDIS
- install redis
- set the redis connection values in main.py

````py
CONST_REDIS_HOST = "localhost"
CONST_REDIS_PORT = 6379
````

## Install SQLserver driver if on linux(debain/ubuntu)

- run the installation script for sql server headers for python

````sh
sudo script_install_debian_reqs.sh
````

- install sql server driver for debain/ubuntu

run

````sh
gdebi-gtk
````

````
to access the gui
click on the files tab to locate the.deb file in this dir and install
````

# RUN

## CONFIGS

````py
CONST_ENV_TEST = True

#the default port for production devices
CONST_DEFAULT_DEVICES_PORT = "8899"
#time in seconds for telnet timeout
#if null value set in the
#tblDAQSettings database table
#the tblDAQSettings database table also has the Sample_time field
#to contron interval of telnet reads
#NOTE the Sample_time value should be more than this value
CONST_DEFAULT_DEVICES_READ_TIMEOUT = 20#secs

#time in seconds
#for consumer workers to pull queued messages from
#redis,parse and write to db
#Telnet read ==interval==> Message Queued in Redis ==CONST_CONSUMER_INTERVAL==> read queued message,parse and save to db
CONST_CONSUMER_INTERVAL = 10#secs

CONST_REDIS_HOST = "localhost"
CONST_REDIS_PORT = 6379

CONST_DATABASE_HOST = "3.221.189.228"
CONST_DATABASE_PORT = 1433
CONST_DATABASE_NAME = 'AmcorData' 
CONST_DATABASE_USERNAME = 'Sa' 
CONST_DATABASE_PASSWORD = "Sheridahill20!"
CONST_DATABASE_URL = "mssql+pyodbc://{}:{}@{}:{}/{}?driver=ODBC+Driver+17+for+SQL+Server".format(
    CONST_DATABASE_USERNAME,
    CONST_DATABASE_PASSWORD,
    CONST_DATABASE_HOST,
    CONST_DATABASE_PORT,
    CONST_DATABASE_NAME
)
````