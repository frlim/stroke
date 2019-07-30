import os
from pathlib import Path
import pandas as pd

if os.name=='nt': #LOCAL
    DTN_FILE = Path('Z:\\stroke_data\\processed_data')/'deidentified_DTN_master.xlsx'
    RES_NAME_PREFIX = Path('F:/stroke_model_output/output_073019')
    HOSPITAL_PATH =Path('data/hospitals/MA_n=1000.csv')
    TIMES_PATH = Path('data/travel_times/MA_n=1000.csv')
else: # FOR TED
    _data_path = Path('/home/hqt2102/deidentified_stroke_data')
    DTN_FILE = _data_path/'deidentified_DTN_master.xlsx'
    RES_NAME_PREFIX  = Path('/sda1/stroke_model_output/output_073019')
    HOSPITAL_PATH = Path('data/hospitals/MA_n=1000.csv')
    TIMES_PATH = Path('data/hospitals/MA_n=1000.csv')


def load_dtn(dtn_file=DTN_FILE):
    return pd.read_excel(dtn_file).set_index('HOSP_KEY')

def load_hospital(hospital_file=HOSPITAL_PATH):
    return pd.read_csv(hospital_file).set_index('HOSP_KEY')

# def load_dtn(dtn_file=DTN_FILE):
#     if os.name=='nt':
#         import xlwings as xw
#         cell_range='A1:M275'
#         sheet = xw.Book(str(dtn_file)).sheets[0]
#         return sheet[cell_range].options(
#             convert=pd.DataFrame, index=False, header=True).value
#     else:
#         return pd.read_excel(dtn_file)
