import pickle
import gzip

with gzip.open('hpcalc_runs/1665784471.14.pkl.gz', 'rb') as f:
    cobj = pickle.load(f)

cobj.df_hourly.write_csv('1665784471.14.df_hourly.csv')
