#*******************************
#IMPORTS python
#*******************************
import os, sys
from concurrent.futures import thread
from copy import copy, deepcopy
from datetime import datetime
from email.policy import default
from gzip import READ
import time,threading
from telnetlib import Telnet
import traceback
from uuid import uuid4

#*******************************
#IMPORTS libs
#*******************************
#Sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,DateTime,NCHAR,
    JSON,Text,Integer,DECIMAL,BIGINT,FLOAT,REAL
)
from sqlalchemy import desc
from sqlalchemy import func
#redis
# import redis
import argparse
# Create the parser
parser = argparse.ArgumentParser()
# Add an argument
parser.add_argument('--deviceID', type=str, required=True)
# Parse the argument
args = parser.parse_args()
deviceID = args.deviceID.upper()


#**************************************************************
#CONSTS
#**************************************************************

CONST_ENV_TEST = False

#the default port for production devices
CONST_DEFAULT_DEVICES_PORT = "8899"
#time in seconds for telnet timeout
#if null value set in the
#tblDAQSettings database table
#the tblDAQSettings database table also has the Sample_time field
#to control interval of telnet reads
#NOTE the Sample_time value should be more than this value
CONST_DEFAULT_TELNET_READ_INTERVAL = 1
CONST_DEFAULT_TELNET_READ_TIMEOUT = 5 # secs

#time in seconds
#for consumer workers to pull queued messages from
#redis,parse and write to db
#Telnet read ==interval==> Message Queued in Redis ==CONST_CONSUMER_INTERVAL==> read queued message,parse and save to db
CONST_CONSUMER_INTERVAL = 2 # secs

# CONST_REDIS_HOST = "localhost"
# CONST_REDIS_PORT = 6379

CONST_DATABASE_HOST = '10.0.0.94'
CONST_DATABASE_PORT = 1433
CONST_DATABASE_NAME = 'AmcorData2'
CONST_DATABASE_USERNAME = 'daqclient'
CONST_DATABASE_PASSWORD = "amcdaq"
CONST_DATABASE_URL = "mssql+pyodbc://{}:{}@{}:{}/{}?driver=ODBC+Driver+17+for+SQL+Server".format(
    CONST_DATABASE_USERNAME,
    CONST_DATABASE_PASSWORD,
    CONST_DATABASE_HOST,
    CONST_DATABASE_PORT,
    CONST_DATABASE_NAME
)

CONST_DATA_EOT = b"EOT"
CONST_DATA_SAMPLE = """
V026b-15CT:5210195192560 wft:0 wfc:0 wfwn:0 wfmn:0.0 wfex:0 wrt:0 wrc:0 wrwn:0
wrmn:0.0 wrex:0 wnt:0 wnc:0 mnt:822809096800 mnc:24020725 ext:783306497232 
exc:175427 exmn:24020692.0 MNipFPM:0.00 exe2:0.0 a1:0 a1t:0 a1c:0 r1ln:0.0 
r1ex:0 rle2:0 r1c:0 a2:0 a2t:0 a2c:0 r2ln:0.0 r2ex:0 r2e2:0 r2c:0 e2t:0 e2c:0 
WnFPM:0.00 ExRPM:0.00 Ex2RPM:0.00 Wfd:0.00 Wrd:0.00 wfrc:0 Wrrc:0 EOT
"""
CONST_DATA_SPLITTER = " "
CONST_DATA_KEYS_TYPES={
    "vCT":{"type":int,"is_count":False},
    "wft":{"type":float,"is_count":False},
    "wfc":{"type":float,"is_count":False},
    "wfwn":{"type":float,"is_count":False},
    "wfmn":{"type":float,"is_count":False},
    "wfex":{"type":float,"is_count":False},
    "wrt":{"type":float,"is_count":False},
    "wrc":{"type":float,"is_count":False},
    "wrwn":{"type":float,"is_count":False},
    "wrmn":{"type":float,"is_count":False},
    "wrex":{"type":float,"is_count":False},
    "wnt":{"type":float,"is_count":False},
    "wnc":{"type":float,"is_count":False},
    "mnt":{"type":float,"is_count":False},
    "mnc":{"type":float,"is_count":False},
    "ext":{"type":float,"is_count":False},
    "exc":{"type":float,"is_count":False},
    "exmn":{"type":float,"is_count":False},
    "MNipFPM":{"type":float,"is_count":False},
    "exe2":{"type":float,"is_count":False},
    "a1":{"type":float,"is_count":False},
    "a1t":{"type":float,"is_count":False},
    "a1c":{"type":float,"is_count":False},
    "r1ln":{"type":float,"is_count":False},
    "r1ex":{"type":float,"is_count":False},
    "rle2":{"type":float,"is_count":False},
    "r1c":{"type":float,"is_count":False},
    "a2":{"type":float,"is_count":False},
    "a2t":{"type":float,"is_count":False},
    "a2c":{"type":float,"is_count":False},
    "r2ln":{"type":float,"is_count":False},
    "r2ex":{"type":float,"is_count":False},
    "r2e2":{"type":float,"is_count":False},
    "r2c":{"type":float,"is_count":False},
    "e2t":{"type":float,"is_count":False},
    "e2c":{"type":float,"is_count":False},
    "WnFPM":{"type":float,"is_count":False},
    "ExRPM":{"type":float,"is_count":False},
    "Ex2RPM":{"type":float,"is_count":False},
    "Wfd":{"type":float,"is_count":False},
    "Wrd":{"type":float,"is_count":False},
    "wfrc":{"type":float,"is_count":False},
    "Wrrc":{"type":float,"is_count":False}
}

CONST_DEFAULT_TEST_SERVERS_DEFAULT_ADDRESS="localhost"
#base port from which range of testing devices telnet are run
CONST_DEFAULT_TEST_SERVERS_DEFAULT_BASE_PORT=8100

READ_DEVICES = {
    "PM0021" : "10.0.3.198",
    "PM0022" : "10.0.3.236",
    "PM0023" : "10.0.3.201",
    "PM0024" : "10.0.3.199",
    "PM0025" : "10.0.3.203",
    "PM0026" : "10.0.3.208",
    "PM0027" : "10.0.3.202",
    "PM0028" : "10.0.3.209",
    "PM0029" : "10.0.3.212",
    "PM0030" : "10.0.3.205",
    "PM0031" : "10.0.3.197",
    "PM0032" : "10.0.3.210",
    "PM0033" : "10.0.3.204"     
}

#**************************************************************
#GLOBAL VARS
#**************************************************************

VAR_SQL_ALCHEMY_ENGINE = None
VAR_SQL_ALCHEMY_DECLARATIVE_BASE=declarative_base()


#**************************************************************
#UTILS
#**************************************************************

def util_log(param_title,param_msg,param_data=None,param_oneline=False):
    """
    util for logging to stdout

    Args:
        :param param_title:
        :param param_msg:
        :param param_data:
    Returns:
        :rtype|void:
    """
    if param_oneline:
        print(
            "TITLE ==> {} | MESSAGES ==> {} | DATA ==> {}".format(
                param_title,
                param_msg,
                param_data
            )
        )
    else:
        print(
        """
        |
        TITLE ==> {}
        |
        MESSAGES ==> {}
        |
        DATA ==> {}
        |
        """.format(
            param_title,
            param_msg,
            param_data
        ))


#**************************************************************
#DATABASE management
#**************************************************************

def util_db_create_engine(param_sqlalch_conn_url):
    """
    get sql alchemy db engine obj
    Args:
        :param param_sqlalch_conn_url: the database connection url
    Returns
        :rtype: sqlalchemy database engine object
    """

    sqlalch_engine = create_engine(param_sqlalch_conn_url)
    return sqlalch_engine

def util_db_create_connection(param_sqlalch_engine):
    """
    get sql alchemy db connection from engine
    mainly used for raw textual SQL queries

    Args:
        :param param_sqlalch_engine: the sqlalchemy engine object
    Returns
        :rtype: sqlalchemy database connection object
    """

    db_conn=param_sqlalch_engine.connect()
    return db_conn

def util_db_create_session_maker(param_sqlalch_engine):
    """
    sql alchemy session object
    get and configure a single main session-maker
    to generate sessions for SqlAlchemy ORM query operations

    Args:
        :param param_sqlalch_engine: the sqlalchemy engine object
    Returns
        :rtype: sqlalchemy session-maker object
    """
    main_session_maker=sessionmaker(bind=param_sqlalch_engine)
    return main_session_maker

def util_db_open_conn_sess(param_sqlalch_conn_url):
    """
    create sqlalch engine,connection,session maker and get session after check database exists

    Args:
        :param param_sqlalch_conn_url: the database connection url
    Returns
        :rtype: sqlalchemy session object and engine object
    """
    try:
        #LOG
        # util_log("DB","CONNECTING TO DB",param_sqlalch_conn_url)
        # print("Connecting to DB... ")

        sqlalch_engine = util_db_create_engine(param_sqlalch_conn_url)
        #sqlalch_connection = util_db_create_connection()
        sqlalch_session_maker = util_db_create_session_maker(sqlalch_engine)
        # create session from maker
        sqlalch_session = sqlalch_session_maker()

        #LOG
        # util_log("DB","CONNECTED TO DB",sqlalch_engine)
        # print("Connected to DB (open conn session)")

        return sqlalch_engine,sqlalch_session
    except Exception as e:
        #LOG
        util_log("DB","ERROR CONNECTING TO DB",str(e))

        return None

def util_db_close_conn_sess(
    param_sqlalch_session,
    param_sqlalch_engine=None,
    param_sqlalch_conn=None,
    param_action_before_close=None):
    """
    roll back the session object and close session, connection and engine

    Args:
        :param param_sqlalch_session: the sqlalchemy session onject
        :param param_sqlalch_engine: the sqlalchemy engine object
        :param param_sqlalch_conn: the sqlalchemy connection object
        :param param_action_before_close|str: action to take before closing the connections
            None|COMMIT|ROLLBACK
    Rturns:
        :rtype|void:
    """
    if param_sqlalch_session is not None:
        if param_action_before_close is not None:
            if param_action_before_close == "ROLLBACK":
                param_sqlalch_session.rollback()
            if param_action_before_close == "COMMIT":
                param_sqlalch_session.commit()
        param_sqlalch_session.close()

    if param_sqlalch_conn is not None:
        param_sqlalch_conn.close()

    if param_sqlalch_engine is not None:
        param_sqlalch_engine.dispose()

def util_sqlalch_row_to_dict(row):
    d = {}
    if row == None:
        return None

    for column in row.__table__.columns:
        if getattr(row, column.name) == None:
            d[column.name] = None
        elif isinstance(getattr(row, column.name),int):
            d[column.name] = int(getattr(row, column.name))
        elif isinstance(getattr(row, column.name),float):
            d[column.name] = float(getattr(row, column.name))
        elif isinstance(getattr(row, column.name),DECIMAL):
            d[column.name] = float(getattr(row, column.name))
        elif isinstance(getattr(row, column.name),FLOAT):
            d[column.name] = float(getattr(row, column.name))
        else:
            d[column.name] = str(getattr(row, column.name))
    return d


#**************************************************************
#REPOSITORY AmcorData
#**************************************************************

class Db_Table_Settings(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "tblDAQSettings"

    Sample_time=Column(Integer,primary_key=True)
    telnet_timeout=Column(Integer)

    @classmethod
    def get_latest(cls,param_sqlalch_session):
        data = param_sqlalch_session.query(cls).first()
        return data

class Db_Table_Production_Devices(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "tblProduction_Devices"

    deviceID=Column(NCHAR, primary_key=True)
    extruderIP=Column(NCHAR)
    current_ex1_lbs_rev=Column(DECIMAL)
    current_ex2_lbs_rev=Column(DECIMAL)
    current_mix_density=Column(FLOAT)

    @classmethod
    def get_all(cls,param_sqlalch_session):
        data = param_sqlalch_session.query(cls).all()
        return data

    @classmethod
    def get_by_ids(cls,param_sqlalch_session,param_ids):
        data = param_sqlalch_session.query(cls).filter(
            cls.deviceID.in_(param_ids)
        )
        return data

    @classmethod
    def get_by_id(cls,param_sqlalch_session,param_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.deviceID == param_id
        ).first()
        return data


class Db_Table_Order_Detail(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "OrderDetail"

    jobID=Column(Integer,primary_key=True)
    ProductID=Column(NCHAR)

    @classmethod
    def get_all(cls,param_sqlalch_session):
        data = param_sqlalch_session.query(cls).all()
        return data

class Db_Table_Finished_Good(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "FinishedGood"

    ID=Column(Integer,primary_key=True)
    ProductID=Column(NCHAR)
    Width=Column(REAL)
    Gusset=Column(FLOAT)

    @classmethod
    def get_all(cls,param_sqlalch_session):
        data = param_sqlalch_session.query(cls).all()
        return data


class Db_Table_Product(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__="Product"

    ID=Column(Integer,primary_key=True)
    ProductID=Column(NCHAR)
    CatID=Column(Integer)

    @classmethod
    def get_cat_id_by_product_id(cls,param_sqlalch_session, param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            Db_Table_Console_Data.prodLineNo == param_device_id).filter(
            Db_Table_Order_Detail.jobID == Db_Table_Console_Data.jobID).filter(
            cls.ProductID == Db_Table_Order_Detail.ProductID
        ).first()
        return data


class Db_Table_Console_Data(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "tblConsole_Data"

    recordID=Column(NCHAR, primary_key=True)
    recordDateTime=Column(DateTime)
    jobID=Column(Integer)
    prodLineNo=Column(NCHAR)
    calculatedGauge=Column(DECIMAL)
    targetGauge=Column(DECIMAL)
    actualLayFlat=Column(DECIMAL)

    @classmethod
    def get_latest_by_device_id(cls,param_sqlalch_session,param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
        ).order_by(desc(cls.recordDateTime)).first()
        return data

    @classmethod
    def get_latest_finished_product_by_device_id(cls,param_sqlalch_session,param_device_id):
        data_console = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
            # cls.prodLineNo == str(deviceID)
        ).order_by(desc(cls.recordDateTime)).first()
        
        data_order_detail = None
        if data_console is not None:
            data_order_detail = param_sqlalch_session.query(Db_Table_Order_Detail).filter(
                Db_Table_Order_Detail.jobID == data_console.jobID
            ).first()

        if data_order_detail is not None:
            data_finished_good = param_sqlalch_session.query(Db_Table_Finished_Good).filter(
                Db_Table_Finished_Good.ProductID == data_order_detail.ProductID
            ).first()
  
            return data_finished_good

        return None

class Db_Table_Data_Log(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "tblProdLines_NetworkData_log"

    recordID=Column(NCHAR,default=uuid4,primary_key=True)
    prodLineNo=Column(NCHAR)
    prodJobID=Column(Integer)
    recordDateTime=Column(DateTime)
    vCT=Column(BIGINT)
    wft=Column(DECIMAL)
    wfc=Column(DECIMAL)
    wfwn=Column(DECIMAL)
    wfmn=Column(DECIMAL)
    wfex=Column(DECIMAL)
    wrt=Column(DECIMAL)
    wrc=Column(DECIMAL)
    wrwn=Column(DECIMAL)
    wrmn=Column(DECIMAL)
    wrex=Column(DECIMAL)
    wnt=Column(DECIMAL)
    wnc=Column(DECIMAL)
    mnt=Column(DECIMAL)
    mnc=Column(DECIMAL)
    ext=Column(DECIMAL)
    exc=Column(DECIMAL)
    exmn=Column(DECIMAL)
    badgeID=Column(NCHAR)
    MNipFPM=Column(DECIMAL)
    exe2=Column(DECIMAL)
    a1=Column(DECIMAL)
    a1t=Column(DECIMAL)
    a1c=Column(DECIMAL)
    r1ln=Column(DECIMAL)
    r1ex=Column(DECIMAL)
    rle2=Column(DECIMAL)
    r1c=Column(DECIMAL)
    a2=Column(DECIMAL)
    a2t=Column(DECIMAL)
    a2c=Column(DECIMAL)
    r2ln=Column(DECIMAL)
    r2ex=Column(DECIMAL)
    r2e2=Column(DECIMAL)
    r2c=Column(DECIMAL)
    e2t=Column(DECIMAL)
    e2c=Column(DECIMAL)
    WnFPM=Column(DECIMAL)
    ExRPM=Column(DECIMAL)
    Ex2RPM=Column(DECIMAL)
    Wfd=Column(DECIMAL)
    Wrd=Column(DECIMAL)
    wfrc=Column(DECIMAL)
    Wrrc=Column(DECIMAL)
    ex1_lbs_rev=Column(DECIMAL)
    ex2_lbs_rev=Column(DECIMAL)
    mix_density=Column(FLOAT)
    calculatedGuage=Column(DECIMAL)
    targetGauge=Column(DECIMAL)
    actualLayFlat=Column(DECIMAL)
    plastic_produced_ratio=Column(DECIMAL)

    @classmethod
    def get_latest_by_device_id(cls,param_sqlalch_session,param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
        ).order_by(desc(cls.recordDateTime)).first()
        return data

#**************************************************************
#APP
#**************************************************************

#PARSED DATA CALCULATORS
def parse_telnet_data(param_data):
    #========================================
    #sanitize data
    #========================================

    sanitized_data = str(param_data).strip()
    sanitized_data = sanitized_data.replace("b'","")
    sanitized_data = sanitized_data.replace("T'","T")
    sanitized_data = sanitized_data.replace(" EOT","")
    sanitized_data = sanitized_data.replace("\\n","")
    sanitized_data = sanitized_data.replace("\\r","")
    sanitized_data = sanitized_data.replace("\n","")
    sanitized_data = sanitized_data.replace("\r","")

    #========================================
    #parse into components
    #========================================

    data_split_list = sanitized_data.split(CONST_DATA_SPLITTER)
    data_split_key_value = {}
    #create dict of values
    for data_key_value in data_split_list:
        if data_key_value.find(":") != -1:
            
            split_map = data_key_value.split(":")

            #handle special case vCT
            #the data key is not the same as the database row
            #so convert
            if split_map[0].find("VO") != -1:
                data_split_key_value["vCT"] = split_map[1]
            elif split_map[0].find("V0") != -1:
                data_split_key_value["vCT"] = split_map[1]
            else:
                data_split_key_value[split_map[0]] = split_map[1]
    return data_split_key_value


def app_parse_calc_plastic_produced(
    param_actual_lay_flat,
    param_finished_good_width,
    param_finished_good_gusset,
    param_cat_id
    ):
    """
    run a parse calculation

    Args:
        :param param_db_data_finished_good|int:
        :param param_finished_good_width|int:
    Returns:
        :rtype|int: calculated value
    """
    if (param_actual_lay_flat==None) or (param_finished_good_width==None) or (param_finished_good_gusset==None):
        return None

    ### DEBUG
    print("\n\n*************")
    print("lay_flat = ", str(param_actual_lay_flat))
    print("width = ", str(param_finished_good_width))
    print("gusset = " + str(param_finished_good_gusset))
    print("cat_id: " + str(param_cat_id))
    # Ex. (int(104/48)*48)/104
    # Add gusset to width for non-single wound jobs
    if param_cat_id == 363 or param_cat_id == 374 or param_cat_id == 559:
        # Single wound jobs trim excess and do not have a gusset.
        print("Single Wound")
        mc = float(param_actual_lay_flat) / float((param_finished_good_width + param_finished_good_gusset))
        print("mc = " + str(mc))
        if mc >= 1:
            mc = int(mc)
        else:
            mc = int(1/(1-mc))
            mc = 1/mc
        #plastic_produced_ratio = float((int(float(param_actual_lay_flat) / param_finished_good_width)* param_finished_good_width) / float(param_actual_lay_flat))
        plastic_produced_ratio = float(mc * (param_finished_good_width + param_finished_good_gusset)) / float(param_actual_lay_flat)
    else:
        # Non single wound jobs may trim one edge and may have a gusset.
        print("Non Single Wound")
        plastic_produced_ratio = 1
    
    print("plastic_produced_ratio = " + str(plastic_produced_ratio))
    print("*************\n\n")
    
    return plastic_produced_ratio

#DATA PARSING

def app_parse_and_save_data(
    param_device_id,
    param_data,
    param_db_engine,
    param_db_session):
    """
    parse device data and save to db

    Args:
        :param param_device_id|str: the device id(also prodLineNo)
        :param param_data|str: the device message
        :param param_db_engine: database connection engine
        :param param_db_session: database connection session
    Returns:
        :rtype|void:
    """

    # Sanitize Data
    data_split_key_value = parse_telnet_data(param_data)

    #========================================
    #retrieve data for compositing
    #========================================

    db_data_device = Db_Table_Production_Devices.get_by_id(
        param_db_session,
        param_device_id
    )
    db_data_device_dict = util_sqlalch_row_to_dict(db_data_device)

    db_data_device_data_log_latest = Db_Table_Data_Log.get_latest_by_device_id(
        param_db_session,
        param_device_id
    )
    db_data_device_data_log_latest_dict = util_sqlalch_row_to_dict(db_data_device_data_log_latest)

    db_data_device_console_latest = Db_Table_Console_Data.get_latest_by_device_id(
        param_db_session,
        param_device_id
    )
    db_data_device_console_latest_dict = util_sqlalch_row_to_dict(db_data_device_console_latest)

    db_data_finished_good = Db_Table_Console_Data.get_latest_finished_product_by_device_id(
        param_db_session,
        param_device_id
    )

    db_data_product = Db_Table_Product.get_cat_id_by_product_id(
        param_db_session,
        param_device_id
    )

    db_data_product_dict = util_sqlalch_row_to_dict(db_data_product)

    new_data_log_row= {}
    if db_data_device_data_log_latest_dict is not None:
        #initialize new data log row
        new_data_log_row = deepcopy(db_data_device_data_log_latest_dict)
        #use default db values for these columns
        new_data_log_row.pop("recordID")
        new_data_log_row["prodJobID"]=db_data_device_console_latest_dict.get("jobID")
    else:
        new_data_log_row["prodLineNo"]=param_device_id
        #new_data_log_row["prodJobID"]=234567
    #use current date
    new_data_log_row["recordDateTime"] = datetime.now()

    #========================================
    #RUN CALCULATIONS
    #AND COMPOSE DATA
    #========================================

    #compare new values to existing
    for data_key,data_value in data_split_key_value.items():

        data_key_value_map = CONST_DATA_KEYS_TYPES.get(data_key,None)
        data_key_value_type = data_key_value_map["type"] if data_key_value_map is not None else data_key_value_map
        data_key_value_is_count = data_key_value_map["is_count"] if data_key_value_map is not None else data_key_value_map

        data_exists_in_db = None
        if db_data_device_data_log_latest_dict is not None:
            data_exists_in_db = db_data_device_data_log_latest_dict.get(data_key,None)

        if data_key_value_type is not None:
            if data_exists_in_db is not None:
                #if data key exists in sensitive numeric values
                if data_key_value_type in [float,int]:

                    data_numeric_new = data_key_value_type(data_value)
                    if data_key_value_type == float:
                        data_numeric_new = round(float(data_numeric_new),2)

                    data_numeric_existing = data_key_value_type(db_data_device_data_log_latest_dict[data_key])
                    if data_key_value_type == float:
                        data_numeric_existing = round(float(data_numeric_existing),2)

                    if (data_key_value_is_count) and (data_numeric_new < data_numeric_existing):
                        #if the value is a count
                        #if new data value is less than existing
                        #add to existing value and add to row
                        new_data_log_row[data_key] = data_numeric_new+data_numeric_existing
                    else:
                        #if new data value is greater than existing
                        #add as new db row
                        new_data_log_row[data_key] = data_numeric_new
            else:
                #if data key exists in sensitive numeric values
                if data_key_value_type in [float,int]:

                    data_numeric_new = data_key_value_type(data_value)
                    if data_key_value_type == float:
                        data_numeric_new = round(float(data_numeric_new),2)

                    new_data_log_row[data_key] = data_numeric_new

    #read from production_device
    ex1 = db_data_device_dict.get("current_ex1_lbs_rev",None)
    ex2 = db_data_device_dict.get("current_ex2_lbs_rev",None)
    mix = float(db_data_device_dict.get("current_mix_density",0.923))
    new_data_log_row["ex1_lbs_rev"] = float(ex1) if ex1 is not None else None
    new_data_log_row["ex2_lbs_rev"] = float(ex2) if ex2 is not None else None
    new_data_log_row["mix_density"] = float(mix) if mix is not None else None

    #read from console_data
    if db_data_device_console_latest_dict is not None:
        calgauge = db_data_device_console_latest_dict.get("calculatedGauge",None)
        targetgauge = db_data_device_console_latest_dict.get("targetGauge",None)
        layflat = db_data_device_console_latest_dict.get("actualLayFlat",None)

        new_data_log_row["plastic_produced_ratio"] = app_parse_calc_plastic_produced(
            db_data_device_console_latest_dict.get("actualLayFlat",None),
            db_data_finished_good.Width if db_data_finished_good is not None else None,
            db_data_finished_good.Gusset if db_data_finished_good is not None else None,
            db_data_product_dict.get("CatID", None)
        )
        new_data_log_row["calculatedGuage"] = float(calgauge) if calgauge is not None else None
        new_data_log_row["targetGauge"] = float(targetgauge) if targetgauge is not None else None
        new_data_log_row["actualLayFlat"] = float(layflat) if layflat is not None else None
    else:
        new_data_log_row["plastic_produced_ratio"] = app_parse_calc_plastic_produced(
            None,
            None,
            None,
            None
        )
        new_data_log_row["calculatedGuage"] = None
        new_data_log_row["targetGauge"] = None
        new_data_log_row["actualLayFlat"] = None

    #========================================
    #SAVE DATA
    #========================================

    try:
        new_data_log_instance = Db_Table_Data_Log(**new_data_log_row)
        param_db_session.add(new_data_log_instance)
        param_db_session.commit()

        #run save new values
        print("\nUPDATED DATA LOG FOR DEVICE_ID: " + param_device_id + "\n")
        # util_log(
        #     "UPDATED DATA LOG",
        #     "DEVICE ==> {}".format(param_device_id),
        #     # new_data_log_row,
        #     param_oneline=True
        # )
    except Exception as e:
        param_db_session.rollback()
        util_log(
            "ERROR UPDATING DATA LOG",
            "DEVICE ==> {}".format(param_device_id),
            "ERROR ==> {}".format(str(e)),
            param_oneline=True
        )


# DATA CAPTURE
def app_telnet_connect_and_read(
    param_device_id,
    param_device_address,
    param_device_index=0):
    """
    connect to a device and read the data

    Args:
        :param param_device_id|str: the device id
        :param param_device_address|str: the device address
        :param param_device_read_interval|int: telnet read interval in milisecs *REMOVED
        :param param_device_read_timeout|int: telnet read timeout in milisecs *REMOVED
    Returns:
        :rtype|void:
    """
    
    # Ping the device to see if it is up before trying to telnet to it.
    ping_device(param_device_id, param_device_address)

    # redis_conn = util_redis_conn()
    telnet_obj = None
    telnet_data = None

    # connect_port = str(CONST_DEFAULT_TEST_SERVERS_DEFAULT_BASE_PORT+param_device_index) if CONST_ENV_TEST else CONST_DEFAULT_DEVICES_PORT
    # connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT if param_device_read_timeout is None else int(param_device_read_timeout/1000)
    connect_port = CONST_DEFAULT_DEVICES_PORT
    connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT

    # Open DB connection
    db_conn_engine,db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)

    while True:
        # telnet_read_interval = float((param_device_read_interval/1000) -1.7)
        telnet_read_interval = CONST_DEFAULT_TELNET_READ_INTERVAL
        
        print("\n\n*** BEGIN TELNET READ LOOP (sleeping for: " + str(telnet_read_interval) + ") ***\n")
        
        time.sleep(telnet_read_interval)

        #TELNET CONNECT
        try:
            # util_log(
            #     "CONNECTING TO DAQ FOR {}".format(param_device_id),
            #     "ADDRESS {}:{}".format(param_device_address,connect_port),
            #     # "INDEX ==> {}".format(param_device_index),
            #     param_oneline=True
            # )
            telnet_obj = Telnet(
                param_device_address,
                connect_port,
                connect_timeout
            )
            util_log(
                "CONNECTED TO DAQ DEVICE_ID: {}".format(param_device_id),
                "ADDRESS {}:{}".format(param_device_address,connect_port),
                # "INDEX ==> {}".format(param_device_index),
                param_oneline=True
            )
        except Exception as tele:
            util_log(
                "ERROR CONNECTING TO DAQ DEVICE_ID: {}".format(param_device_id),
                "ADDRESS {}:{}".format(param_device_address,connect_port),
                # "INDEX ==> {}".format(param_device_index),
                param_oneline=True
            )

        #TELNET READ
        try:
            while True:
                if telnet_obj is not None:
                    telnet_data = telnet_obj.read_until(CONST_DATA_EOT).decode('ascii')
                    if str(telnet_data).find("V0") != -1:
                        #QUEUE READ DATA

                        util_log(
                            "GOOD READ FROM DAQ DEVICE_ID: {} (telnet read interval: {})".format(param_device_id,telnet_read_interval),
                            "ADDRESS {}:{}".format(param_device_address,connect_port),
                            param_data=("\n" + telnet_data),
                            param_oneline=True
                        )

                        if telnet_data not in [None,""]:
                            app_parse_and_save_data(
                                param_device_id,
                                telnet_data,
                                db_conn_engine,
                                db_conn_session
                            )

                        telnet_obj.close()
                        break
                    else:
                        # util_log(
                        #     "*** BAD READ FROM DAQ DEVICE_ID: {} (telnet read interval: {}),DISCARDING DATA (check telnet_read_interval)".format(param_device_id,telnet_read_interval),
                        #     "ADDRESS {}:{} INDEX {}".format(param_device_address,connect_port,param_device_index),
                        #     # param_data=telnet_data,
                        #     param_oneline=True
                        # )
                        pass
        except Exception as e:
            print(e)
            # util_log(
            #     "READ ERROR FROM DAQ DEVICE_ID: {}".format(param_device_id),
            #     "ADDRESS {}:{} INDEX {}".format(param_device_address,connect_port,param_device_index),
            #     param_data=str(e),
            #     param_oneline=True
            # )
        print("*** END TELNET READ LOOP ***\n")
    # else:
    #     # Ping fail returns exit code 256
    #     print(param_device_id + " is not responding. Restarting loop.")
    #     telnet_obj = None
    #     telnet_data = None
    #     time.sleep(10)
    #     app_telnet_connect_and_read(
    #     param_device_id,
    #     param_device_address,
    #     param_device_index=0)


# Startup Functions
def ping_device(param_device_id, param_device_address):
    # Ping the device to see if it is up before trying to telnet to it.
    print("Pinging device...")
    ping_cmd = "ping -c 1 -W 3 " + param_device_address
    ping_device = os.system(ping_cmd)
    if not ping_device == 0:
        count = 10
        print("Device not responding. Waiting " + str(count) + " seconds...")
        time.sleep(count)
        print("Restarting DAQ service for " + param_device_id + "...")
        os.system("sudo systemctl restart daq-" + param_device_id.lower() + ".service")
        sys.exit()
    else:
        print("Device is up. Continuing...")
        

def get_single_telnet_data_record(deviceID):
    tn_data_good = None
    tn_obj = Telnet(READ_DEVICES[deviceID], 8899, 3)
    while True:
        tn_data = tn_obj.read_until(b"EOT").decode("ascii")
        if str(tn_data).find("V0") != -1:
            tn_data_good = tn_data
            break
        else:
            time.sleep(1)
    tn_obj.close()
    return tn_data_good


def get_exc_exe2_from_single_telnet_data_record(tn_data):
    data = parse_telnet_data(tn_data)
    exc = data["exc"]
    exe2 = data["exe2"]
    return exc, exe2


def app_correct_extruder_count():
    print("\nGetting extruder counts ...")
    # Get the current extruder count from the DAQ box.
    print("Getting exc_box_last ...")
    tn_data_last = get_single_telnet_data_record(deviceID)
    exc_box_last, exe2_box_last = get_exc_exe2_from_single_telnet_data_record(tn_data_last)

    # Get the current extruder count from the DB.
    print("Getting exc_db_last ...")
    db_conn_engine, db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)
    db_data_device_data_log_latest = Db_Table_Data_Log.get_latest_by_device_id(
        db_conn_session,
        deviceID
    )
    exc_db_last = int(db_data_device_data_log_latest.exc)
    exe_db_last = int(db_data_device_data_log_latest.exe2)

    # Close DB Connection
    util_db_close_conn_sess(
        db_conn_session,
        param_sqlalch_engine=db_conn_engine
    )

    sleep_time = 3
    print("Letting extruder cycle for " + str(sleep_time) + " seconds ...\n")
    time.sleep(sleep_time)

    print("Getting exc_box_current ...")
    tn_data_current = get_single_telnet_data_record(deviceID)
    exc_box_current, exe2_box_current = get_exc_exe2_from_single_telnet_data_record(tn_data_current)

    exc_box_delta = int(exc_box_current) - int(exc_box_last)
    # exc_box_last = exc_box_current
    new_exc = exc_db_last + exc_box_delta
    
    print("\nResults for " + deviceID + ": ")
    print("   exc_box_last: ", str(exc_box_last))
    print("exc_box_current: ", str(exc_box_current))
    print("    exc_db_last: ", str(exc_db_last))
    print("  exc_box_delta: ", str(exc_box_delta))
    print("        new_exc: ", str(new_exc))
    print("\n")
    exc_box_last = exc_box_current
    exc_db_last = new_exc


def app_start_listeners():
    """
    start a telnet listener for all devices
    retrieved from the db

    Returns:
        :rtype|list: list of threads
    """

    # open db connection
    db_conn_engine,db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)
   
    app_telnet_connect_and_read(
        deviceID,
        READ_DEVICES[deviceID])

    # close db connection
    util_db_close_conn_sess(
        db_conn_session,
        param_sqlalch_engine=db_conn_engine
    )


def run():
    """
    run main
    """
    ping_device(deviceID, param_device_address=READ_DEVICES[deviceID])
    app_correct_extruder_count()
    app_start_listeners()



if __name__ == "__main__":
    run()