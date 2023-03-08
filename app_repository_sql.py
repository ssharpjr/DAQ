#**************************************************************
# IMPORTS
#**************************************************************
from uuid import uuid4

#SQLAlchemy
from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,DateTime,NCHAR,
    JSON,Text,Integer,DECIMAL,BIGINT,FLOAT,REAL
)
from sqlalchemy import text, desc
# from sqlalchemy import func


#**************************************************************
# CONSTANTS
#**************************************************************
VAR_SQL_ALCHEMY_ENGINE = None
VAR_SQL_ALCHEMY_DECLARATIVE_BASE=declarative_base()


#**************************************************************
# REPOSITORY AmcorData
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
    DAQexc=Column(DECIMAL)
    DAQexe2=Column(DECIMAL)
    DAQmnc=Column(DECIMAL)

    # DateTime to use for getting the MAX() records
    # dt = '2022-07-25 06:00:00.000'
    dt = '2022-08-01 06:00:00.000'

    @classmethod
    def get_latest_by_device_id(cls,param_sqlalch_session,param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
        ).order_by(desc(cls.recordDateTime)).first()
        return data


    @classmethod
    def get_max_exc_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(exc)
            from tblProdLines_NetworkData_log
            where exc in ( 
                select top (100000) exc
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        # result = param_sqlalch_session.execute(sql, {'pm': param_device_id, 'dt': cls.dt})
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data


    @classmethod
    def get_max_exe2_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(exe2)
            from tblProdLines_NetworkData_log
            where exe2 in ( 
                select top (100000) exe2
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data

    
    @classmethod
    def get_max_mnc_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(mnc)
            from tblProdLines_NetworkData_log
            where mnc in ( 
                select top (100000) mnc
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data


class Db_Table_Data_Log_Archive(VAR_SQL_ALCHEMY_DECLARATIVE_BASE):

    __tablename__= "tblProdLines_NetworkData_log_ARCHIVE"

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
    DAQexc=Column(DECIMAL)
    DAQexe2=Column(DECIMAL)
    DAQmnc=Column(DECIMAL)

    # DateTime to use for getting the MAX() records
    # dt = '2022-07-25 06:00:00.000'
    dt = '2022-08-01 06:00:00.000'

    @classmethod
    def get_latest_by_device_id(cls,param_sqlalch_session,param_device_id):
        data = param_sqlalch_session.query(cls).filter(
            cls.prodLineNo == param_device_id
        ).order_by(desc(cls.recordDateTime)).first()
        return data


    @classmethod
    def get_max_exc_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(exc)
            from tblProdLines_NetworkData_log
            where exc in ( 
                select top (100000) exc
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        # result = param_sqlalch_session.execute(sql, {'pm': param_device_id, 'dt': cls.dt})
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data


    @classmethod
    def get_max_exe2_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(exe2)
            from tblProdLines_NetworkData_log
            where exe2 in ( 
                select top (100000) exe2
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data

    
    @classmethod
    def get_max_mnc_by_device_id(cls,param_sqlalch_session,param_device_id):
        sql = text("""
            select max(mnc)
            from tblProdLines_NetworkData_log
            where mnc in ( 
                select top (100000) mnc
                from tblProdLines_NetworkData_log
                where prodLineNo = :pm
                order by recordDateTime desc
                )
            """)
        result = param_sqlalch_session.execute(sql, {'pm': param_device_id})
        for r in result:
            # Only returns 1 row
            data = r[0]
        return data