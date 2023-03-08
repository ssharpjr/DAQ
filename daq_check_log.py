#! /usr/bin/env python3
# -*- coding: UTF-8 -*-


from datetime import datetime
from sqlalchemy import create_engine, text



CONST_DATABASE_HOST = '10.0.0.94'
CONST_DATABASE_PORT = 1433
CONST_DATABASE_NAME = 'AmcorData_SS'
CONST_DATABASE_USERNAME = 'daqclient'
CONST_DATABASE_PASSWORD = "amcdaq"
CONST_DATABASE_URL = "mssql+pyodbc://{}:{}@{}:{}/{}?driver=ODBC+Driver+17+for+SQL+Server".format(
    CONST_DATABASE_USERNAME,
    CONST_DATABASE_PASSWORD,
    CONST_DATABASE_HOST,
    CONST_DATABASE_PORT,
    CONST_DATABASE_NAME
)



engine = create_engine(CONST_DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("select top(1) prodLineNo, recordDateTime from tblProdLines_NetworkData_log where prodLineNo = 'PM0021' order by recordDateTime desc"))
    for r in result:
        x = r.recordDateTime
        c = datetime.now()
        
        print(x.strftime("%Y-%m-%d %H:%M:%S"))
        print("    Current: ", str(c.strftime("%s")))
        print("Last Record: ", x.strftime("%s"))
        print("      Delta: ", c-x)
