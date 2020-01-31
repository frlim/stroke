import numpy as np
from stroke import constants
import pandas as pd
import paths
import scipy.stats as stats

n_patients = 1000

age_median,age_iqr = 74,(61,82)
age_std = np.mean([age_median-age_iqr[0],age_iqr[1]-age_median])/(0.6745)

nihss_mean,nihss_std = 8.2,8

female_p = 0.54

time_median,time_iqr = 164,(65,475)
time_std = (time_median-time_iqr[0])/(0.6745)

def random_age():
    age =  np.random.normal(loc=age_median,scale=age_std)
    if age > 99: age = 99
    return int(np.round(age))

def random_nihss():
    score = np.random.normal(loc=nihss_mean,scale=nihss_std)
    if score < 0: score = 0
    if score > 42: score = 42
    return int(np.round(score))

def skew_nihss():
    score= stats.skewnorm.rvs(a=5,loc=-3.2,scale=nihss_std*1.73)
    if score < 0: score = 0
    if score > 42: score = 42
    return int(np.round(score))

def random_sex():
    return np.random.choice(a=list(constants.Sex),p=[1-female_p,female_p])

def random_time():
    distributions = [np.random.uniform(low=0,high=time_iqr[0]),
    np.random.uniform(low=time_iqr[0],high=time_median),
    np.random.uniform(low=time_median,high=time_iqr[1]),
    np.random.uniform(low=time_iqr[1],high=time_iqr[1]+1.5*(time_iqr[1]-time_iqr[0]))]
    time =  np.random.choice(distributions)
    return int(np.round(time))
    
# test the distribution
q75, median, q25 = np.percentile([random_time() for i in range(n_patients)], [75 ,50, 25])
q25, median,q75

ls = [skew_nihss() for i in range(n_patients*10)]
np.mean(ls),np.std(ls)


patient_records = [{'age':random_age(),'nihss':skew_nihss(),'sex':random_sex(),'time_since_symptoms':random_time()} for i in range(n_patients)]
patient_df = pd.DataFrame.from_records(patient_records)
patient_df.index.name = 'ID'
patient_df.describe()

patient_df.to_csv(paths._data_path/'patient_profiles_01_30_20.csv')

df = pd.read_csv(paths._data_path/'patient_profiles_01_30_20.csv',index_col=0)
df.head()
df.describe()
