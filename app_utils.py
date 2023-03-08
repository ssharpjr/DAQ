#**************************************************************
# IMPORTS
#**************************************************************
import os, sys
# import logging

# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,DateTime,NCHAR,
    JSON,Text,Integer,DECIMAL,BIGINT,FLOAT,REAL
)


# logging.basicConfig(level=logging.DEBUG, filename='test.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

#**************************************************************
# UTILS
#**************************************************************

def restart_daq(param_device_id):
    print("Restarting DAQ service for " + param_device_id + "...")
    # os.system("sudo systemctl restart daq-" + param_device_id.lower() + ".service")
    sys.exit()


def log_list(param_title, param_msg):
    print("['{}', {}]".format(param_title, param_msg))


def util_log(param_title,param_msg,param_data=None,param_oneline=True,param_log_level="info"):
    """
    util for logging to stdout

    Args:
        :param param_title:
        :param param_msg:
        :param param_data:
    Returns:
        :rtype|void:
    """
    level = param_log_level
    if param_oneline:
        # logging.info("{}: {}: {}".format(param_title, param_msg, param_data))
        print(
            "{} | {}".format(
                param_title,
                param_msg
                # param_data
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

def util_db_open_conn_sess(param_sqlalch_conn_url, param_device_id):
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
        restart_daq(param_device_id)


def util_db_close_conn_sess(
    param_sqlalch_session,
    param_sqlalch_engine=None,
    param_sqlalch_conn=None,
    param_action_before_close=None):
    """
    roll back the session object and close session, connection and engine

    Args:
        :param param_sqlalch_session: the sqlalchemy session object
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