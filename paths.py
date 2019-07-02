import os
from pathlib import Path
import pandas as pd

if os.name=='nt': #LOCAL
    DTN_FILE = Path('Z:\\stroke_data')/'deidentified_DTN.xlsx'
    RES_NAME_PREFIX = Path('E:/stroke_model_output/output_070219')
    HOSPITAL_PATH =Path('data/hospitals/MA_n=100.csv')
    TIMES_PATH = Path('data/travel_times/MA_n=100.csv')
else: # FOR TED
    _data_path = Path('/home/hqt2102/deidentified_stroke_data')
    DTN_FILE = _data_path/'deidentified_DTN_uc.xlsx'
    RES_NAME_PREFIX  = _data_path/'output/output_070219'
    HOSPITAL_PATH = _data_path/'hospitals/MA_n=100.csv'
    TIMES_PATH = _data_path/'travel_times/MA_n=100.csv'

def load_dtn(dtn_file=DTN_FILE):
    if os.name=='nt':
        import xlwings as xw
        cell_range='A1:M275'
        sheet = xw.Book(str(dtn_file)).sheets[0]
        return sheet[cell_range].options(
            convert=pd.DataFrame, index=False, header=True).value
    else:
        return pd.read_excel(dtn_file)
