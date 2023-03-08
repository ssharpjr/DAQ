#*******************************
# IMPORTS python
#*******************************
import os, sys, time, argparse
from socket import timeout
from copy import deepcopy
from datetime import datetime
from telnetlib import Telnet
# from uuid import uuid4

#*******************************
# IMPORTS modules
#*******************************
from app_utils import *
from app_repository_sql import *


#**************************************************************
# CONSTS
#**************************************************************
CONST_ENV_TEST = False

# The default port for production devices
CONST_DEFAULT_DEVICES_PORT = "8899"
# Time in seconds for telnet timeout
# If null value set in the
# tblDAQSettings database table
# the tblDAQSettings database table also has the Sample_time field
# to control interval of telnet reads
# NOTE the Sample_time value should be more than this value
CONST_DEFAULT_TELNET_READ_INTERVAL = 1
CONST_DEFAULT_TELNET_READ_TIMEOUT = 5 # secs

# Time in seconds
# for consumer workers to pull queued messages from
# redis,parse and write to db
# Telnet read ==interval==> Message Queued in Redis ==CONST_CONSUMER_INTERVAL==> read queued message,parse and save to db
CONST_CONSUMER_INTERVAL = 2 # secs

# CONST_REDIS_HOST = "localhost"
# CONST_REDIS_PORT = 6379

CONST_DATABASE_HOST = '10.0.0.94'
CONST_DATABASE_PORT = 1433
CONST_DATABASE_NAME = 'AmcorData'
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
# Base port from which range of testing devices telnet are run
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
# GLOBAL VARS
#**************************************************************
EXC_BOX_LAST = None
EXE2_BOX_LAST = None
EXC_DB_LAST = None
EXE2_DB_LAST = None


#**************************************************************
# APP
#**************************************************************

# Create Arg Parser
parser = argparse.ArgumentParser()
# Add an argument
parser.add_argument('--deviceID', type=str, required=True)
# Parse the argument
args = parser.parse_args()
deviceID = args.deviceID.upper()

# PARSED DATA CALCULATORS
def parse_telnet_data(param_data, single_run=None):
    #========================================
    # Sanitize data
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
    # Parse into components
    #========================================

    data_split_list = sanitized_data.split(CONST_DATA_SPLITTER)
    data_split_key_value = {}
    # Create dict of values
    for data_key_value in data_split_list:
        if data_key_value.find(":") != -1:
            
            split_map = data_key_value.split(":")

            # Handle special case vCT
            # the data key is not the same as the database row
            # so convert
            if split_map[0].find("VO") != -1:
                data_split_key_value["vCT"] = split_map[1]
            elif split_map[0].find("V0") != -1:
                data_split_key_value["vCT"] = split_map[1]
            else:
                data_split_key_value[split_map[0]] = split_map[1]
    
    
    if not single_run:
        # Update exc and exe2 from global vars on each loop iteration
        global EXC_BOX_LAST
        global EXC_DB_LAST
        global EXE2_BOX_LAST
        global EXE2_DB_LAST
        exc_box_current = data_split_key_value["exc"]
        print("\n******************************")
        print("  exc_box_current: ", str(exc_box_current))
        print("     EXC_BOX_LAST: ", str(EXC_BOX_LAST))
        exc_box_delta = float(exc_box_current) - float(EXC_BOX_LAST)
        new_exc = EXC_DB_LAST + exc_box_delta
        EXC_BOX_LAST = exc_box_current
        print("    exc_box_delta: ", exc_box_delta)
        print("\n      EXC_DB_LAST: ", str(EXC_DB_LAST))
        print("          new_exc: ", str(new_exc))
        data_split_key_value["exc"] = new_exc
        EXC_DB_LAST = new_exc
        print("  New EXC_DB_LAST: ", str(EXC_DB_LAST))
        print(" New EXC_BOX_LAST: ", str(EXC_BOX_LAST))

        exe2_box_current = data_split_key_value["exe2"]
        print("\n exe2_box_current: ", str(exe2_box_current))
        print("    EXE2_BOX_LAST: ", str(EXE2_BOX_LAST))
        exe2_box_delta = float(exe2_box_current) - float(EXE2_BOX_LAST)
        new_exe2 = EXE2_DB_LAST + exe2_box_delta
        EXE2_BOX_LAST = exe2_box_current
        print("   exe2_box_delta: ", exe2_box_delta)
        print("\n     EXE2_DB_LAST: ", str(EXE2_DB_LAST))
        print("         new_exe2: ", str(new_exe2))
        data_split_key_value["exe2"] = new_exe2
        EXE2_DB_LAST = new_exe2
        print(" New EXE2_DB_LAST: ", str(EXE2_DB_LAST))
        print("New EXE2_BOX_LAST: ", str(EXE2_BOX_LAST))
        print("******************************")
        # print(data_split_key_value)

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
    print("\n\n******************************")
    print("lay_flat: ", str(param_actual_lay_flat))
    print("   width: ", str(param_finished_good_width))
    print("  gusset: ", str(param_finished_good_gusset))
    print("  cat_id: ", str(param_cat_id))
    # Ex. (int(104/48)*48)/104
    # Add gusset to width for non-single wound jobs
    if param_cat_id == 363 or param_cat_id == 374 or param_cat_id == 559:
        # Single wound jobs trim excess and do not have a gusset.
        print("Single Wound (CatID: " + str(param_cat_id) + ")")

        # If roll is larger than lay flat, just return a 1
        if float(param_finished_good_width) > float(param_actual_lay_flat):
            plastic_produced_ratio = 1
            return plastic_produced_ratio
        else:
            # Calculate multi-count
            mc = float(param_actual_lay_flat) / float((param_finished_good_width + param_finished_good_gusset))
            print("      Multi-Count (mc): ", str(mc))
            if mc >= 1:
                mc = int(mc)
            else:
                mc = int(1/(1-mc))
                mc = 1/mc
        
        plastic_produced_ratio = float((mc * (param_finished_good_width + param_finished_good_gusset))) / float(param_actual_lay_flat)
    else:
        # Non single wound jobs may trim one edge and may have a gusset.
        print("Non Single Wound")
        plastic_produced_ratio = 1
    
    print("plastic_produced_ratio: ", str(plastic_produced_ratio))
    print("\n******************************\n\n")
    
    return plastic_produced_ratio

# DATA PARSING

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
    # Retrieve data for compositing
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
        # Initialize new data log row
        new_data_log_row = deepcopy(db_data_device_data_log_latest_dict)
        # Use default db values for these columns
        new_data_log_row.pop("recordID")
        new_data_log_row["prodJobID"]=db_data_device_console_latest_dict.get("jobID")
    else:
        new_data_log_row["prodLineNo"]=param_device_id
        # new_data_log_row["prodJobID"]=234567
    # Use current date
    new_data_log_row["recordDateTime"] = datetime.now()

    #========================================
    # RUN CALCULATIONS
    # AND COMPOSE DATA
    #========================================

    # Compare new values to existing
    for data_key,data_value in data_split_key_value.items():

        data_key_value_map = CONST_DATA_KEYS_TYPES.get(data_key,None)
        data_key_value_type = data_key_value_map["type"] if data_key_value_map is not None else data_key_value_map
        data_key_value_is_count = data_key_value_map["is_count"] if data_key_value_map is not None else data_key_value_map

        data_exists_in_db = None
        if db_data_device_data_log_latest_dict is not None:
            data_exists_in_db = db_data_device_data_log_latest_dict.get(data_key,None)

        if data_key_value_type is not None:
            if data_exists_in_db is not None:
                # If data key exists in sensitive numeric values
                if data_key_value_type in [float,int]:

                    data_numeric_new = data_key_value_type(data_value)
                    if data_key_value_type == float:
                        data_numeric_new = round(float(data_numeric_new),2)

                    data_numeric_existing = data_key_value_type(db_data_device_data_log_latest_dict[data_key])
                    if data_key_value_type == float:
                        data_numeric_existing = round(float(data_numeric_existing),2)

                    if (data_key_value_is_count) and (data_numeric_new < data_numeric_existing):
                        # If the value is a count
                        # If new data value is less than existing
                        # add to existing value and add to row
                        new_data_log_row[data_key] = data_numeric_new+data_numeric_existing
                    else:
                        # If new data value is greater than existing
                        # add as new db row
                        new_data_log_row[data_key] = data_numeric_new
            else:
                # If data key exists in sensitive numeric values
                if data_key_value_type in [float,int]:

                    data_numeric_new = data_key_value_type(data_value)
                    if data_key_value_type == float:
                        data_numeric_new = round(float(data_numeric_new),2)

                    new_data_log_row[data_key] = data_numeric_new
   
    # Read from production_device
    ex1 = db_data_device_dict.get("current_ex1_lbs_rev",None)
    ex2 = db_data_device_dict.get("current_ex2_lbs_rev",None)
    mix = float(db_data_device_dict.get("current_mix_density",0.923))
    new_data_log_row["ex1_lbs_rev"] = float(ex1) if ex1 is not None else None
    new_data_log_row["ex2_lbs_rev"] = float(ex2) if ex2 is not None else None
    new_data_log_row["mix_density"] = float(mix) if mix is not None else None

    # Read from console_data
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
    # SAVE DATA
    #========================================

    try:
        new_data_log_instance = Db_Table_Data_Log(**new_data_log_row)
        param_db_session.add(new_data_log_instance)
        param_db_session.commit()

        # Run save new values
        # print("\nUPDATED DATA LOG FOR DEVICE_ID: " + param_device_id + "\n")
        util_log(
            "UPDATED DATA LOG",
            "DEVICE ==> {}".format(param_device_id),
            new_data_log_row,
            param_oneline=True
        )
    except Exception as e:
        param_db_session.rollback()
        util_log(
            "ERROR UPDATING DATA LOG",
            "DEVICE ==> {}".format(param_device_id),
            "ERROR ==> {}".format(str(e)),
            param_oneline=True
        )
        print("Restarting DAQ service for " + param_device_id + "...")
        os.system("sudo systemctl restart daq-" + param_device_id.lower() + ".service")
        sys.exit()


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
    # ping_device(param_device_id, param_device_address)

    telnet_obj = None
    telnet_data = None

    # connect_port = str(CONST_DEFAULT_TEST_SERVERS_DEFAULT_BASE_PORT+param_device_index) if CONST_ENV_TEST else CONST_DEFAULT_DEVICES_PORT
    # connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT if param_device_read_timeout is None else int(param_device_read_timeout/1000)
    connect_port = CONST_DEFAULT_DEVICES_PORT
    connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT

    # Open DB connection
    db_conn_engine,db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)

    count = 0
    # while count == 0:
    while True:
        # telnet_read_interval = float((param_device_read_interval/1000) -1.7)
        telnet_read_interval = CONST_DEFAULT_TELNET_READ_INTERVAL
        
        print("\n\n*** BEGIN TELNET READ LOOP (sleeping for: " + str(telnet_read_interval) + ") ***\n")
        
        # Ping the device to see if it is up before trying to telnet to it.
        # ping_device(param_device_id, param_device_address)

        time.sleep(telnet_read_interval)

        # TELNET CONNECT
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

        # TELNET READ
        try:
            while True:
                if telnet_obj is not None:
                    telnet_data = telnet_obj.read_until(CONST_DATA_EOT).decode('ascii')
                    if str(telnet_data).find("V0") != -1:
                        # QUEUE READ DATA

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
        count = 1


# Startup Functions
def ping_device(param_device_id, param_device_address):
    # Ping the device to see if it is up before trying to telnet to it.
    print("Pinging Telnet device...")
    ping_cmd = "ping -c 1 -W 3 " + param_device_address
    ping_device = os.system(ping_cmd)
    if not ping_device == 0:
        count = 1
        print("Telnet device not responding. Restarting in " + str(count) + " seconds...")
        time.sleep(count)
        print("Restarting DAQ service for " + param_device_id + "...")
        os.system("sudo systemctl restart daq-" + param_device_id.lower() + ".service")
        sys.exit()
    else:
        print("\nTelnet device is up. Continuing...")
        

def get_single_telnet_data_record(deviceID):
    tn_data_good = None
    tn_obj = Telnet(READ_DEVICES[deviceID], 8899, 3)
    while True:
        try:
            tn_data = tn_obj.read_until(b"EOT").decode("ascii")
            if str(tn_data).find("V0") != -1:
                tn_data_good = tn_data
                break
            else:
                time.sleep(1)
        except Exception as e:
            print("Telnet connection timed out")
            print("Restarting DAQ service for " + deviceID + "...")
            os.system("sudo systemctl restart daq-" + deviceID.lower() + ".service")
            sys.exit()
    tn_obj.close()
    return tn_data_good


def get_exc_exe2_from_single_telnet_data_record(tn_data):
    data = parse_telnet_data(tn_data, single_run=True)
    exc = float(data["exc"])
    exe2 = float(data["exe2"])
    return exc, exe2


def app_set_global_extruder_counts():
    print("\n******************************")
    print("Getting extruder counts")
    # Get the current extruder counts (exc, exe2) from the DAQ box.
    print("Getting exc_box_last ...")
    tn_data_last = get_single_telnet_data_record(deviceID)
    exc_box_last, exe2_box_last = get_exc_exe2_from_single_telnet_data_record(tn_data_last)
    print(" exc_box_last (initial read): " + str(exc_box_last))
    print("exe2_box_last (initial read): " + str(exe2_box_last))

    # Get the current extruder count from the DB.
    print("\nGetting exc_db_last ...")
    db_conn_engine, db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)
    db_data_device_data_log_latest = Db_Table_Data_Log.get_latest_by_device_id(
        db_conn_session,
        deviceID
    )
    exc_db_last = float(db_data_device_data_log_latest.exc)
    exe2_db_last = float(db_data_device_data_log_latest.exe2)
    print(" exc_db_last (initial read): " + str(exc_db_last))
    print("exe2_db_last (initial read): " + str(exe2_db_last))

    # Negative count failsafe
    if exc_db_last < 0:
        exc_db_last = 0
        print("*** exc_db_last has been reset to ZERO! ***")
        print(" exc_db_last (reset): " + str(exc_db_last))
    if exe2_db_last < 0:
        exe2_db_last = 0
        print("*** exe2_db_last has been reset to ZERO! ***")
        print(" exe2_db_last (reset): " + str(exe2_db_last))

    ######################################################################
    # Get the max extruder counts from the DB.
    # print("\nGetting max extruder counts from the DB ...")
    # exc_db_max = float(Db_Table_Data_Log.get_max_exc_by_device_id(
    #     db_conn_session,
    #     deviceID
    # ))
    # exe2_db_max = float(Db_Table_Data_Log.get_max_exe2_by_device_id(
    #     db_conn_session,
    #     deviceID
    # ))
    
    # print(" exc_db_max (initial read): " + str(exc_db_max))
    # print("exe2_db_max (initial read): " + str(exe2_db_max))
    # print("\n")
    
    # Informational only at this time
    # if exc_db_max > exc_db_last:
    #     print("exc_db_max is greater than exc_db_last")
    # elif exc_db_max == exc_db_last:
    #     print("exc_db_last matches exc_db_last")
    
    # if exe2_db_max > exe2_db_last:
    #     print("exe2_db_max is greater than exe2_db_last")
    # elif exe2_db_max == exe2_db_last:
    #     print("exe2_db_last matches exe2_db_last")

    # Close DB Connection
    util_db_close_conn_sess(
        db_conn_session,
        param_sqlalch_engine=db_conn_engine
    )

    sleep_time = 3
    print("\nLetting extruders cycle for " + str(sleep_time) + " seconds ...\n")
    time.sleep(sleep_time)

    print("Getting exc_box_current ...")
    tn_data_current = get_single_telnet_data_record(deviceID)
    exc_box_current, exe2_box_current = get_exc_exe2_from_single_telnet_data_record(tn_data_current)
    print(" exc_box_current (initial read): " + str(exc_box_current))
    print("exe2_box_current (initial read): " + str(exe2_box_current))

    exc_box_delta = float(exc_box_current) - float(exc_box_last)
    exe2_box_delta = float(exe2_box_current) - float(exe2_box_last)
    new_exc = exc_db_last + exc_box_delta
    new_exe2 = exe2_db_last + exe2_box_delta
    # new_exc = exc_db_max + exc_box_delta
    # new_exe2 = exe2_db_max + exe2_box_delta
    
    print("\n******************************")
    print("\nResults for " + deviceID + ": ")
    print("    exc_box_last: ", str(exc_box_last))
    print(" exc_box_current: ", str(exc_box_current))
    print("   exc_box_delta: ", str(exc_box_delta))
    print("     exc_db_last: ", str(exc_db_last))
    # print("     exc_db_max: ", str(exc_db_max))
    print("         new_exc: ", str(new_exc))
    print("")
    print("   exe2_box_last: ", str(exe2_box_last))
    print("exe2_box_current: ", str(exe2_box_current))
    print("  exe2_box_delta: ", str(exe2_box_delta))
    print("    exe2_db_last: ", str(exe2_db_last))
    # print("     exe2_db_max: ", str(exe2_db_max))
    print("        new_exe2: ", str(new_exe2))
    print("\n******************************")
    print("\n")
    exc_box_last = exc_box_current
    exe2_box_last = exe2_box_current
    exc_db_last = new_exc
    exe2_db_last = new_exe2
    return exc_box_last, exe2_box_last, exc_db_last, exe2_db_last


def app_start_listeners():
    """
    start a telnet listener for all devices
    retrieved from the db

    Returns:
        :rtype|list: list of threads
    """

    # Open db connection
    db_conn_engine,db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)
   
    app_telnet_connect_and_read(
        deviceID,
        READ_DEVICES[deviceID])

    # Close db connection
    util_db_close_conn_sess(
        db_conn_session,
        param_sqlalch_engine=db_conn_engine
    )


def run():
    """
    run main
    """
    os.system("clear")
    print("\nStarting Data Acquisition App for DeviceID: " + str(deviceID) + "\n")
    ping_device(deviceID, param_device_address=READ_DEVICES[deviceID])
    exc_box_last, exe2_box_last, exc_db_last, exe2_db_last = app_set_global_extruder_counts()
    global EXC_BOX_LAST
    global EXE2_BOX_LAST
    global EXC_DB_LAST
    global EXE2_DB_LAST
    EXC_BOX_LAST = exc_box_last
    EXE2_BOX_LAST = exe2_box_last
    EXC_DB_LAST = exc_db_last
    EXE2_DB_LAST = exe2_db_last

    app_start_listeners()


if __name__ == "__main__":
    run()
