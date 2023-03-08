#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

#############################
# IMPORTS
#############################
import time
from datetime import datetime
from uuid import uuid4

# SQL-Alchemy
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,DateTime,NCHAR,
    JSON,Text,Integer,DECIMAL,BIGINT,FLOAT,REAL
)
from sqlalchemy import desc


# CONSTANTS
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


# GLOBAL VARS
VAR_SQL_ALCHEMY_ENGINE = None
VAR_SQL_ALCHEMY_DECLARATIVE_BASE=declarative_base()


# Database Management
def util_db_create_engine(param_sqlalch_conn_url):
    sqlalch_engine = create_engine(param_sqlalch_conn_url)
    return sqlalch_engine


def util_db_create_connection(param_sqlalch_engine):
    db_conn=param_sqlalch_engine.connect()
    return db_conn


def util_db_create_session_maker(param_sqlalch_engine):
    main_session_maker=sessionmaker(bind=param_sqlalch_engine)
    return main_session_maker


def util_db_open_conn_sess(param_sqlalch_conn_url):
    try:
        sqlalch_engine = util_db_create_engine(param_sqlalch_conn_url)
        sqlalch_session_maker = util_db_create_session_maker(sqlalch_engine)
        sqlalch_session = sqlalch_session_maker()
        print("Connected to DB")
        return sqlalch_engine, sqlalch_session
    except Exception as e:
        print("Error connecting to DB", str(e))
        return None


def util_db_close_conn_sess(
    param_sqlalch_session,
    param_sqlalch_engine=None,
    param_sqlalch_conn=None,
    param_action_before_close=None):
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


# DB Repositories
class Db_Table_Data_log(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__ = "tblProdLines_NetworkData_log"

    recordID=Column(NCHAR,primary_key=True)
    prodLineNo=Column(NCHAR)
    recordDateTime=Column(DateTime)
    exc=Column(DECIMAL)

    @classmethod
    def get_latest_by_device_id(cls,param_sqlalch_session,param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
        ).order_by(desc(cls.recordDateTime)).first()
        return data
    
    @classmethod
    def get_latest_exc_by_device_id(cls,param_sqlalch_session,param_device_id):
        # Get the max 'exc' from 2022-07-01 to present
        dt = '20220708 00:00:00.000'
        sql = text("""
            select max(exc)
            from tblProdLines_NetworkData_log
            where exc in ( 
				select exc
				from tblProdLines_NetworkData_log
				where prodLineNo = :pm
				and recordDateTime >= :dt
				)
        """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id, 'dt': dt})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data
    

    @classmethod
    def get_latest_exe2_by_device_id(cls,param_sqlalch_session,param_device_id):
        # Get the max 'exc' from 2022-07-01 to present
        dt = '20220708 00:00:00.000'
        sql = text("""
            select max(exe2)
            from tblProdLines_NetworkData_log
            where exe2 in ( 
                select exe2
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                and recordDateTime >= :dt
                )
            """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id, 'dt': dt})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data


# Get Data
def get_latest_data_log(param_db_session, param_device_id):
    db_data_log = Db_Table_Data_log.get_latest_by_device_id(
        param_db_session,
        param_device_id
    )
    print(type(db_data_log))

    db_data_log_dict = util_sqlalch_row_to_dict(db_data_log)

    prod_line = db_data_log_dict.get("prodLineNo")
    record_dt = db_data_log_dict.get("recordDateTime")
    print("     Prod Line = ", str(prod_line))
    print("RecordDateTime = ", str(record_dt))

# Get max exc
def get_max_exc(param_db_session, param_device_id):
    db_data_log = Db_Table_Data_log.get_latest_exc_by_device_id(
        param_db_session,
        param_device_id
    )

    max_exc = db_data_log
    return max_exc


# Get max exe2
def get_max_exe2(param_db_session, param_device_id):
    db_data_log = Db_Table_Data_log.get_latest_exe2_by_device_id(
        param_db_session,
        param_device_id
    )

    max_exe2 = db_data_log
    return max_exe2

    
def main():
    db_conn_engine, db_conn_session = util_db_open_conn_sess(CONST_DATABASE_URL)
    # get_latest_data_log(db_conn_session, "PM0028")
    max_exc = get_max_exc(db_conn_session, "PM0028")
    max_exe2 = get_max_exe2(db_conn_session, "PM0028")
    print(" Max exc: ", str(max_exc))
    print("Max exe2: ", str(max_exe2))


if __name__ == '__main__':
    main()
