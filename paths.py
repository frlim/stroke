import os
from pathlib import Path
import pandas as pd

if os.name=='nt': #LOCAL
    _data_path = Path('Z:\\stroke_data\\processed_data')
    DTN_FILE = _data_path/'deidentified_DTN_master_v2.xlsx'
    RES_NAME_PREFIX = Path('F:/stroke_model_output/output_102919')
    HOSPITAL_PATH = Path('data/hospitals/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')
    TIMES_PATH = Path('data/travel_times/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')
else: # FOR TED
    _data_path = Path('/home/hqt2102/deidentified_stroke_data')
    DTN_FILE = _data_path/'deidentified_DTN_master_v2.xlsx'
    RES_NAME_PREFIX  = Path('/sda1/stroke_model_output/output_102919')
    HOSPITAL_PATH = Path('data/hospitals/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')
    TIMES_PATH = Path('data/travel_times/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')

# for local MAC, work from home
# _data_path = Path.home()/'Stroke_scripts'/'network_data'
_data_path = Path('/Volumes/DOM_DGM_HUR$/stroke_data')/ 'processed_data'
# door-to-needle times (sensitive data - hospitals de-identified)
DTN_FILE = _data_path/'deidentified_DTN_master_v3.xlsx'
# directory to save model's output (need a lot of storage space)
RES_NAME_PREFIX = Path.home()/'Stroke_scripts/stroke_model_output/output_071520'
# path to travel times
HOSPITAL_PATH = Path('data/hospitals/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')
TIMES_PATH = Path('data/travel_times/NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv')


DTN_COLS = ['IVTPA_P25', 'IVTPA_MEDIAN', 'IVTPA_P75','IVTPA_N']
DTP_COLS = ['IATPA_P25', 'IATPA_MEDIAN', 'IATPA_P75','IATPA_N']

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
