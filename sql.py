from sqlalchemy import *

def getRate(zip_code):
    engine = create_engine('mysql+pymysql://root@localhost/sustainable?charset=utf8&use_unicode=0', pool_recycle=3600)
    connection = engine.connect()
    sql_command = "SELECT zip, resrate FROM utilities WHERE zip = '{0}'".format(zip_code)
    result = engine.execute(sql_command)
    return(row['resrate'])
    result.close()