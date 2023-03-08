#*******************************
# IMPORTS python
#*******************************
import os, sys, time, argparse
import logging
from socket import timeout
from copy import deepcopy
from datetime import datetime
from telnetlib import Telnet
from pythonping import ping
from app_repository_sql import Db_Table_Product, Db_Table_Console_Data, Db_Table_Data_Log

#*******************************
# IMPORTS modules
#*******************************
from app_utils import *
from app_repository_sql import *


#************************************************************************
# CONSTS
#************************************************************************

# Set Runtime Operators
DEBUG = False
LOGGING = True

CONST_DEFAULT_DEVICES_PORT = "8899"
CONST_DEFAULT_TELNET_READ_INTERVAL = 1
CONST_DEFAULT_TELNET_READ_TIMEOUT = 5 # secs
CONST_CONSUMER_INTERVAL = 2 # secs

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

# DAQ Telnet devices
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


#************************************************************************
# GLOBAL VARS
#************************************************************************

STARTUP_last_db_DAQexc = None
STARTUP_last_db_DAQexe2 = None
STARTUP_last_db_DAQmnc = None
STARTUP_MAX_DB_EXC = None
STARTUP_MAX_DB_EXE2 = None
STARTUP_MAX_DB_MNC = None


#************************************************************************
# APP
#************************************************************************

# Create Arg Parser
parser = argparse.ArgumentParser(
    prog = os.path.basename(__file__),
    description = "Captures and stores data acquired from an ESP32 microcontroller",
    epilog = "@2022 Amcor, Inc.\n"
)
# Add an argument
parser.add_argument('-d', '--device', type=str, required=True,
                    help='PM Asset Tag of the Line control panel. (EX: PM0000)')

# Parse the argument
args = parser.parse_args()
deviceID = args.device.upper()

# Create Logger
log_file = "log/" + deviceID + ".log"
logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# PARSED DATA CALCULATORS
def parse_telnet_data(param_data, single_run=None, startup_run=None):
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
    if DEBUG:
        print("\n\n******************************")
        print("lay_flat: ", str(param_actual_lay_flat))
        print("   width: ", str(param_finished_good_width))
        print("  gusset: ", str(param_finished_good_gusset))
        print("  cat_id: ", str(param_cat_id))
    # Ex. (int(104/48)*48)/104
    # Add gusset to width for non-single wound jobs
    if param_cat_id == 363 or param_cat_id == 374 or param_cat_id == 559:
        # Single wound jobs trim excess and do not have a gusset.
        if DEBUG:
            print("Single Wound (CatID: " + str(param_cat_id) + ")")

        # If roll is larger than lay flat, just return a 1
        if float(param_finished_good_width) > float(param_actual_lay_flat):
            plastic_produced_ratio = 1
            return plastic_produced_ratio
        else:
            # Calculate multi-count
            mc = float(param_actual_lay_flat) / float((param_finished_good_width + param_finished_good_gusset))
            if DEBUG:
                print("      Multi-Count (mc): ", str(mc))
            if mc >= 1:
                mc = int(mc)
            else:
                mc = int(1/(1-mc))
                mc = 1/mc
        
        plastic_produced_ratio = float((mc * (param_finished_good_width + param_finished_good_gusset))) / float(param_actual_lay_flat)
    else:
        # Non single wound jobs may trim one edge and may have a gusset.
        # print("Non Single Wound")
        plastic_produced_ratio = 1
    
    # print("plastic_produced_ratio: ", str(plastic_produced_ratio))
    # print("\n******************************\n\n")
    
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

    db_data_device = Db_Table_Production_Devices.get_by_id(param_db_session, param_device_id)
    db_data_device_data_log_latest = Db_Table_Data_Log.get_latest_by_device_id(param_db_session, param_device_id)
    db_data_device_console_latest = Db_Table_Console_Data.get_latest_by_device_id(param_db_session, param_device_id)
    db_data_finished_good = Db_Table_Console_Data.get_latest_finished_product_by_device_id(param_db_session, param_device_id)
    db_data_product = Db_Table_Product.get_cat_id_by_product_id(param_db_session, param_device_id)

    db_data_device_dict = util_sqlalch_row_to_dict(db_data_device)
    db_data_device_data_log_latest_dict = util_sqlalch_row_to_dict(db_data_device_data_log_latest)
    db_data_device_console_latest_dict = util_sqlalch_row_to_dict(db_data_device_console_latest)
    db_data_product_dict = util_sqlalch_row_to_dict(db_data_product)

    new_data_log_row= {}
    if db_data_device_data_log_latest_dict is not None:
        # Initialize new data log row
        new_data_log_row = deepcopy(db_data_device_data_log_latest_dict)
        # Use default db values for these columns
        new_data_log_row.pop("recordID")
        new_data_log_row["prodJobID"] = db_data_device_console_latest_dict.get("jobID")
    else:
        new_data_log_row["prodLineNo"] = param_device_id
        # new_data_log_row["prodJobID"]=234567
    # Use current date
    new_data_log_row["recordDateTime"] = datetime.now()

    #========================================
    # RUN CALCULATIONS
    # AND COMPOSE DATA
    #========================================

    # Read from global variables
    global STARTUP_last_db_DAQexc
    global STARTUP_last_db_DAQexe2
    global STARTUP_last_db_DAQmnc
    global STARTUP_MAX_DB_EXC
    global STARTUP_MAX_DB_EXE2
    global STARTUP_MAX_DB_MNC

    # Assign local variables
    current_daq_box_exc = float(data_split_key_value["exc"])
    last_DAQexc = float(STARTUP_last_db_DAQexc)
    max_db_exc = float(STARTUP_MAX_DB_EXC)
    
    current_daq_box_exe2 = float(data_split_key_value["exe2"])
    last_DAQexe2 = float(STARTUP_last_db_DAQexe2)
    max_db_exe2 = float(STARTUP_MAX_DB_EXE2)

    current_daq_box_mnc = float(data_split_key_value["mnc"])
    last_daq_box_mnc = float(STARTUP_last_db_DAQmnc)
    max_db_mnc = float(STARTUP_MAX_DB_MNC)


    # Calculate deltas
    if DEBUG:
        print("\nCalculating deltas...")
    if LOGGING:
        logging.debug("CALCULATING_DELTAS")
    exc_delta = None
    exe2_delta = None
    mnc_delta = None
    
    # EXC Delta
    if current_daq_box_exc >= last_DAQexc:
        # The current DAQ box count is the highest number (positive result).
        # The DAQ box has not rebooted.
        # The delta is the difference of the current DAQ box reading and the last DB record.
        if DEBUG:
            print("(No reboot detected)")
        exc_delta = current_daq_box_exc - last_DAQexc
        if LOGGING:
            logging.debug("+ EXC_DELTA: {} (exc delta = current daq box exc - last daq exc)".format(exc_delta))
    else:
        # The DAQexe value in the DB is higher (negative result).
        # The DAQ box has rebooted, so the count has reset. 
        # The current DAQ box count is the number of cycles since startup.
        # The delta is the current DAQ box count.
        if DEBUG:
            print("(Reboot detected. Using current DAQ box count as the delta.)")
        exc_delta = current_daq_box_exc
        if LOGGING:
            logging.debug("+ EXC_DELTA: {} ( = current daq box exc) [REBOOT DETECTED]".format(exc_delta))
    
    # # EXE2 Delta
    if current_daq_box_exe2 >= max_db_exe2:
        exe2_delta = current_daq_box_exe2 - last_DAQexe2
        if LOGGING:
            logging.debug("+ EXE2_DELTA: {} ( = current daq box exe2 - last daq exe2)".format(exe2_delta))
    else:
        exe2_delta = current_daq_box_exe2
        if LOGGING:
            logging.debug("+ EXE2_DELTA: {} ( = current daq box exe2)".format(exe2_delta))
    
    # # MNC Delta
    if current_daq_box_mnc >= max_db_mnc:
        mnc_delta = current_daq_box_mnc - last_daq_box_mnc
        if LOGGING:
            logging.debug("+ MNC_DELTA: {} ( = current daq box mnc - last daq mnc)".format(mnc_delta))
    else:
        mnc_delta = current_daq_box_mnc
        if LOGGING:
            logging.debug("+ MNC_DELTA: {} ( = current daq box mnc)".format(mnc_delta))

    # Insert the new values into the existing data structures
    new_exc = max_db_exc + exc_delta
    data_split_key_value["exc"] = new_exc
    db_data_device_data_log_latest_dict.update(DAQexc=current_daq_box_exc)

    new_exe2 = max_db_exe2 + exe2_delta
    data_split_key_value["exe2"] = new_exe2
    db_data_device_data_log_latest_dict.update(DAQexe2=current_daq_box_exe2)

    new_mnc = max_db_mnc + mnc_delta
    data_split_key_value["mnc"] = new_mnc
    db_data_device_data_log_latest_dict.update(DAQmnc=current_daq_box_mnc)

    # DEBUG
    if DEBUG:
        print("\n************************************************************")
        print("         current_daq_box_exc: " + str(current_daq_box_exc))
        print("                 last_DAQexc: " + str(last_DAQexc))
        print("                  max_db_exc: " + str(max_db_exc))
        print("                   exc_delta: " + str(exc_delta))
        print("                     new_exc: " + str(new_exc))
        print("")
        print("        current_daq_box_exe2: " + str(current_daq_box_exe2))
        print("                last_DAQexe2: " + str(last_DAQexe2))
        print("                 max_db_exe2: " + str(max_db_exe2))
        print("                  exe2_delta: " + str(exe2_delta))
        print("                    new_exe2: " + str(new_exe2))
        print("")
        print("         current_daq_box_mnc: " + str(current_daq_box_mnc))
        print("            last_daq_box_mnc: " + str(last_daq_box_mnc))
        print("                  max_db_mnc: " + str(max_db_mnc))
        print("                   mnc_delta: " + str(mnc_delta))
        print("                     new_mnc: " + str(new_mnc))
        print("")
        print("      Old STARTUP_MAX_DB_EXC: " + str(STARTUP_MAX_DB_EXC))
        print("  Old STARTUP_last_db_DAQexc: " + str(STARTUP_last_db_DAQexc))
        print("")
        print("     Old STARTUP_MAX_DB_EXE2: " + str(STARTUP_MAX_DB_EXE2))
        print(" Old STARTUP_last_db_DAQexe2: " + str(STARTUP_last_db_DAQexe2))
        print("")
        print("      Old STARTUP_MAX_DB_MNC: " + str(STARTUP_MAX_DB_MNC))
        print("  Old STARTUP_last_db_DAQmnc: " + str(STARTUP_last_db_DAQmnc))
    
    if LOGGING:
        logging.debug("+ NEW_EXC: {} (max db exc + exc delta)".format(new_exc))
        logging.debug("+ NEW_EXE2: {} (max db exe2 + exe2 delta)".format(new_exe2))
        logging.debug("+ NEW_MNC: {} (max db mnc + mnc delta)".format(new_mnc))

    # Update global variables
    STARTUP_MAX_DB_EXC = new_exc
    STARTUP_last_db_DAQexc = current_daq_box_exc
    STARTUP_MAX_DB_EXE2 = new_exe2
    STARTUP_last_db_DAQexe2 = current_daq_box_exe2
    STARTUP_MAX_DB_MNC = new_mnc
    STARTUP_last_db_DAQmnc = current_daq_box_mnc

    if DEBUG:
        print("------------------------------------------------------------")
        print("      New STARTUP_MAX_DB_EXC: " + str(STARTUP_MAX_DB_EXC))
        print("  New STARTUP_last_db_DAQexc: " + str(STARTUP_last_db_DAQexc))
        print("")
        print("     New STARTUP_MAX_DB_EXE2: " + str(STARTUP_MAX_DB_EXE2))
        print(" New STARTUP_last_db_DAQexe2: " + str(STARTUP_last_db_DAQexe2))
        print("")
        print("      New STARTUP_MAX_DB_MNC: " + str(STARTUP_MAX_DB_MNC))
        print("  New STARTUP_last_db_DAQmnc: " + str(STARTUP_last_db_DAQmnc))
        print("************************************************************\n")


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
                        new_data_log_row[data_key] = data_numeric_new + data_numeric_existing
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

    # Update Network Log
    daqexc = db_data_device_data_log_latest_dict.get("DAQexc", None)
    daqexe2 = db_data_device_data_log_latest_dict.get("DAQexe2", None)
    daqmnc = db_data_device_data_log_latest_dict.get("DAQmnc", None)
    new_data_log_row["DAQexc"] = float(daqexc) if daqexc is not None else None
    new_data_log_row["DAQexe2"] = float(daqexe2) if daqexe2 is not None else None
    new_data_log_row["DAQmnc"] = float(daqmnc) if daqmnc is not None else None

    #========================================
    # SAVE DATA
    #========================================

    try:
        new_data_log_instance = Db_Table_Data_Log(**new_data_log_row)
        param_db_session.add(new_data_log_instance)
        param_db_session.commit()
        # print("\n\n*** SAVE DISABLED ***\n\n")
        # if LOGGING:
        #     logging.warning("SAVE_DISABLED. No data written to database.")

        # Run save new values
        # print("\nUPDATED DATA LOG FOR DEVICE_ID: " + param_device_id + "\n")
        log_list("DB_UPDATE", new_data_log_row)

        # util_log(
        #     "UPDATED DB FOR: {}".format(param_device_id),
        #     new_data_log_row,
        #     param_oneline=True
        # )
    except Exception as e:
        # param_db_session.rollback()
        util_db_close_conn_sess(param_action_before_close="ROLLBACK")
        util_log(
            "ERROR UPDATING DB FOR: {}".format(param_device_id),
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
    # ping_device(param_device_id, param_device_address)

    telnet_obj = None
    telnet_data = None

    # connect_port = str(CONST_DEFAULT_TEST_SERVERS_DEFAULT_BASE_PORT+param_device_index) if CONST_ENV_TEST else CONST_DEFAULT_DEVICES_PORT
    # connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT if param_device_read_timeout is None else int(param_device_read_timeout/1000)
    connect_port = CONST_DEFAULT_DEVICES_PORT
    connect_timeout = CONST_DEFAULT_TELNET_READ_TIMEOUT

    # Open DB connection
    db_conn_engine,db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL, deviceID)

    # count = 2
    # while count >= 0:
    while True:
        # telnet_read_interval = float((param_device_read_interval/1000) -1.7)
        telnet_read_interval = CONST_DEFAULT_TELNET_READ_INTERVAL
        
        if DEBUG:
            print("\n\n*** BEGIN TELNET READ LOOP (sleeping for: " + str(telnet_read_interval) + ") ***\n")
        if LOGGING:
            logging.debug("APP_LOOP_START: {}".format(deviceID))
        
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

            # if LOGGING:
            #     logging.debug("TELNET_CONNECT_SUCCESS: telnet object created")
            # util_log(
            #     "CONNECTED TO DAQ DEVICE_ID: {}".format(param_device_id),
            #     "ADDRESS {}:{}".format(param_device_address,connect_port),
            #     # "INDEX ==> {}".format(param_device_index),
            #     param_oneline=True
            # )
        except Exception as tele:
            util_log(
                "ERROR CONNECTING TO DAQ DEVICE_ID: {}".format(param_device_id),
                "ADDRESS {}:{}".format(param_device_address,connect_port),
                # "INDEX ==> {}".format(param_device_index),
                param_oneline=True
            )
            if LOGGING:
                logging.debug("TELNET_CONNECT_FAILED: Failed to create telnet object.")

        # TELNET READ
        try:
            while True:
                if telnet_obj is not None:
                    telnet_data = telnet_obj.read_until(CONST_DATA_EOT).decode('ascii')
                    if str(telnet_data).find("V0") != -1:
                        # QUEUE READ DATA

                        # util_log(
                        #     "GOOD READ FROM DAQ DEVICE_ID: {} (telnet read interval: {})".format(param_device_id,telnet_read_interval),
                        #     "ADDRESS {}:{}".format(param_device_address,connect_port),
                        #     param_data=("\n" + telnet_data),
                        #     param_oneline=True
                        # )

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
        if DEBUG:
            print("\n*** END TELNET READ LOOP ***\n")
        if LOGGING:
            logging.debug("APP_LOOP_END")
        # count = count - 1


# Startup Functions
def ping_device(param_device_id, param_device_address):
    # Ping the device to see if it is up before trying to telnet to it.
    # if LOGGING:
    #     logging.debug("{}: {} ({})".format("PINGING_DEVICE", param_device_id, param_device_address))
    device_up = False
    while not device_up:
        resp = ping(param_device_address, count=2, timeout=1)
        if resp.success() == False:
            if DEBUG:
                print("{} is not responding. Retrying...".format(param_device_id))
            if LOGGING:
                logging.warning("{}: {} ({})".format("PING_FAILED", param_device_id, param_device_address))
            time.sleep(1)
        else:
            if LOGGING:
                logging.debug("{}: {} ({})".format("PING_SUCCESS", param_device_id, param_device_address))
            break
    device_up = True


def get_single_telnet_data_record(deviceID):
    tn_data_good = None
    tn_obj = Telnet(READ_DEVICES[deviceID], 8899, 3)
    # if LOGGING:
    #     logging.debug("STARTUP_GET_SINGLE_TELNET_DATA_RECORD")
    while True:
        try:
            tn_data = tn_obj.read_until(b"EOT").decode("ascii")
            if str(tn_data).find("V0") != -1:
                tn_data_good = tn_data
                # if LOGGING:
                #     logging.debug("{}".format("SUCCESS_GET_SINGLE_TELNET_DATA_RECORD"))
                break
            else:
                # if LOGGING:
                #     logging.debug("{}".format("FAILED_GET_SINGLE_TELNET_DATA_RECORD. Trying again."))
                time.sleep(1)
        except Exception as e:
            if DEBUG:
                print("Cannot connect to Telnet device: {}".format(deviceID))
                print(e)
            if LOGGING:
                logging.critical("FAILED_GET_SINGLE_TELNET_DATA_RECORD: {}".format(e))
            # print("Telnet connection timed out")
            # print("Restarting DAQ service for " + deviceID + "...")
            # os.system("sudo systemctl restart daq-" + deviceID.lower() + ".service")
            # sys.exit()
    tn_obj.close()
    return tn_data_good


def get_counts_from_single_telnet_data_record(tn_data):
    data = parse_telnet_data(tn_data)
    exc = float(data["exc"])
    exe2 = float(data["exe2"])
    mnc = float(data["mnc"])
    return exc, exe2, mnc


def set_global_counts_on_startup():
    # print("\n**********************************************************************")
    print("Getting counts")
    
    # Get counts from the DAQ box.
    print("\nGetting DAQ box counts ...")
    if LOGGING:
        logging.debug("GETTING_DAQ_BOX_COUNTS")

    tn_data_last = get_single_telnet_data_record(deviceID)
    current_daq_box_exc, current_daq_box_exe2, current_daq_box_mnc = get_counts_from_single_telnet_data_record(tn_data_last)
    if DEBUG:
        print("current_daq_box_exc", current_daq_box_exc)
        print("current_daq_box_exe2", current_daq_box_exe2)
        print("current_daq_box_mnc", current_daq_box_mnc)
    if LOGGING:
        logging.debug("+ current_daq_box_exc: {}".format(current_daq_box_exc))
        logging.debug("+ current_daq_box_exe2: {}".format(current_daq_box_exe2))
        logging.debug("+ current_daq_box_mnc: {}".format(current_daq_box_mnc))

    # Get the counts from the DB.
    print("\nGetting database counts ...")
    if LOGGING:
        logging.debug("GETTING_DB_COUNTS")
    db_conn_engine, db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL, deviceID)
    db_data_device_data_log_latest = Db_Table_Data_Log.get_latest_by_device_id(db_conn_session, deviceID)
    
    # If DAQexc is NULL in the DB, use the current DAQ box count.
    if DEBUG:
        print("last_db_DAQexc...")
    try:
        last_db_DAQexc = float(db_data_device_data_log_latest.DAQexc)
    except:
        if DEBUG:
            print("*** (DAQexc not found. Using current DAQ box count.) ***")
        if LOGGING:
            logging.debug("- DAQexc not found. Using current DAQ box count.")
        last_db_DAQexc = current_daq_box_exc
    if LOGGING:
        logging.debug("+ last_db_DAQexc: {}".format(last_db_DAQexc))

    if DEBUG:
        print("last_db_DAQexe2...")
    try:
        last_db_DAQexe2 = float(db_data_device_data_log_latest.DAQexe2)
    except:
        if DEBUG:
            print("*** (DAQexe2 not found. Using current DAQ box count.) ***")
        if LOGGING:
            logging.debug("- DAQexe2 not found. Using current DAQ box count.")
        last_db_DAQexe2 = current_daq_box_exe2
    if LOGGING:
        logging.debug("+ last_db_DAQexe2: {}".format(last_db_DAQexe2))

    if DEBUG:
        print("last_db_DAQmnc...")
    try:
        last_db_DAQmnc = float(db_data_device_data_log_latest.DAQmnc)
    except:
        if DEBUG:
            print("*** (DAQmnc not found. Using current DAQ box count.) ***")
        if LOGGING:
            logging.debug("- DAQmnc not found. Using current DAQ box count.")
        last_db_DAQmnc = current_daq_box_mnc
    if LOGGING:
        logging.debug("+ last_db_DAQmnc: {}".format(last_db_DAQmnc))

    if DEBUG:
        print("max_db_exc...")
    max_db_exc = float(Db_Table_Data_Log.get_max_exc_by_device_id(db_conn_session, deviceID))
    if LOGGING:
        logging.debug("+ max_db_exc: {}".format(max_db_exc))
    if DEBUG:
        print("max_db_exe2...")
    max_db_exe2 = float(Db_Table_Data_Log.get_max_exe2_by_device_id(db_conn_session, deviceID))
    if LOGGING:
        logging.debug("+ max_db_exe2: {}".format(max_db_exe2))
    if DEBUG:
        print("max_db_mnc...")
    max_db_mnc = float(Db_Table_Data_Log.get_max_mnc_by_device_id(db_conn_session, deviceID))
    if LOGGING:
        logging.debug("+ max_db_mnc: {}".format(max_db_mnc))
    util_db_close_conn_sess(db_conn_session, param_sqlalch_engine=db_conn_engine)

    # Set globals
    global STARTUP_last_db_DAQexc
    global STARTUP_last_db_DAQexe2
    global STARTUP_last_db_DAQmnc
    global STARTUP_MAX_DB_EXC
    global STARTUP_MAX_DB_EXE2
    global STARTUP_MAX_DB_MNC

    STARTUP_last_db_DAQexc = last_db_DAQexc
    STARTUP_last_db_DAQexe2 = last_db_DAQexe2
    STARTUP_last_db_DAQmnc = last_db_DAQmnc
    STARTUP_MAX_DB_EXC = max_db_exc
    STARTUP_MAX_DB_EXE2 = max_db_exe2
    STARTUP_MAX_DB_MNC = max_db_mnc

    # Print results
    if DEBUG:
        print("\n**********************************************************************")
        print(" current_daq_box_exc (initial read): " + str(current_daq_box_exc))
        print("      last_db_DAQexc (initial read): " + str(last_db_DAQexc))
        print("          max_db_exc (initial read): " + str(max_db_exc))
        print("")
        print("current_daq_box_exe2 (initial read): " + str(current_daq_box_exe2))
        print("     last_db_DAQexe2 (initial read): " + str(last_db_DAQexe2))
        print("         max_db_exe2 (initial read): " + str(max_db_exe2))
        print("")
        print(" current_daq_box_mnc (initial read): " + str(current_daq_box_mnc))
        print("      last_db_DAQmnc (initial read): " + str(last_db_DAQmnc))
        print("          max_db_mnc (initial read): " + str(max_db_mnc))
        print("")
        print("             STARTUP_last_db_DAQexc: " + str(STARTUP_last_db_DAQexc))
        print("                 STARTUP_MAX_DB_EXC: " + str(STARTUP_MAX_DB_EXC))
        print("            STARTUP_last_db_DAQexe2: " + str(STARTUP_last_db_DAQexe2))
        print("                STARTUP_MAX_DB_EXE2: " + str(STARTUP_MAX_DB_EXE2))
        print("             STARTUP_last_db_DAQmnc: " + str(STARTUP_last_db_DAQmnc))
        print("                 STARTUP_MAX_DB_MNC: " + str(STARTUP_MAX_DB_MNC))
        print("**********************************************************************")
    if LOGGING:
        logging.debug("+ STARTUP_last_db_DAQexc: {}".format(STARTUP_last_db_DAQexc))
        logging.debug("+ STARTUP_MAX_DB_EXC: {}".format(STARTUP_MAX_DB_EXC))
        logging.debug("+ STARTUP_last_db_DAQexe2: {}".format(STARTUP_last_db_DAQexe2))
        logging.debug("+ STARTUP_MAX_DB_EXE2: {}".format(STARTUP_MAX_DB_EXE2))
        logging.debug("+ STARTUP_last_db_DAQmnc: {}".format(STARTUP_last_db_DAQmnc))
        logging.debug("+ STARTUP_MAX_DB_MNC: {}".format(STARTUP_MAX_DB_MNC))


def app_exit_ki(param_db_session=None):
    if DEBUG:
        print("\nKeyboardInterrupt detected. Closing session and exiting.\n")
    if LOGGING:
        logging.warning("KEYBOARD_INTERRUPT_DETECTED: EXITING")
    util_db_close_conn_sess(param_db_session)
    sys.exit()


def run_app():
    """
    run main
    """
    # os.system("clear") -- systemd doesn't like this...
    print("\nStarting Data Acquisition (DAQ) App for DeviceID: " + str(deviceID) + "\n")

    if LOGGING:
        logging.debug("APP_STARTING: {}".format(deviceID))

    # Report which DB is being used.
    if CONST_DATABASE_NAME != "AmcorData":
        if DEBUG:
            print("WARNING: LIVE DATABASE IS NOT SELECTED!")
            print("{} database is currently in use.\n".format(CONST_DATABASE_NAME))
        if LOGGING:
            logging.warning("WARNING: LIVE DATABASE IS NOT SELECTED!")
            logging.warning("{} database is currently in use.".format(CONST_DATABASE_NAME))

    # Check that the device is reachable
    ping_device(deviceID, param_device_address=READ_DEVICES[deviceID])
    
    # Set startup global variables
    set_global_counts_on_startup()
    if LOGGING:
        logging.debug("APP_STARTUP_COMPLETE")

    # Start the loop
    print("\nDAQ loop running")
    app_telnet_connect_and_read(deviceID, READ_DEVICES[deviceID])


def main():
    try:
        run_app()
    except KeyboardInterrupt:
        app_exit_ki()

if __name__ == "__main__":
    main()
