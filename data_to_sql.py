import sqlalchemy as sqlal
from pathlib import Path
import xlwings as xw
import data_io
import pandas as pd

# Purpose: load hospital performance data in form of password protected Excel sheets
# into a SQL server
# Requirement: PostgreSQL need an empty database
# make one with CREATE DATABASE [database_name]
# enter in login credentials for the SQL sever in

# Make a SQL connection
def create_engine():
    DB = 'stroke' # name of database
    HOST = 'localhost' # might need to change to name of the host workstation
    USER = 'postgres'# default PostgreSQL
    PORT='5432' # default PostgreSQ
    PASSWORD = 'largevesselocclusion' # created during installation
    engine= sqlal.create_engine(
    f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}')
    return engine

engine = create_engine()

# Check to make sure connection works
meta = sqlal.MetaData()
meta.reflect(engine)
meta.tables.keys()

# Read excel files to be sent to SQL server
# KORI_GRANT.xlsx is original data file, isn't used directly by the model 
data_path = Path('E:\\stroke_data')
filename = 'deidentified_DTN.xlsx'
df = data_io._load_dtn_file(data_path/filename)
df.to_sql('dtn',engine,if_exists='replace',index=False)


filename = 'hospital_keys.xlsx'
sheet = xw.Book(str(data_path/filename) ).sheets[0]
df = sheet['A1:C275'].options(convert=pd.DataFrame,index=False,header=True).value
df.to_sql('hosp_key',engine,if_exists='replace',index=False)


filename = 'AHA 2012 ID codes.xlsx'
sheet = xw.Book(str(data_path/filename) ).sheets[0]
df = sheet['A1:F108'].options(convert=pd.DataFrame,index=False,header=False).value
df.columns = ['AHA_ID','Name','Street','City','ZIP','State']
df['AHA_ID']=df['AHA_ID'].astype(int)
df.to_sql('hosp_address',engine,if_exists='replace',index=False)

#verify that the tables have been inserted
meta.reflect(engine)
meta.tables.keys()
