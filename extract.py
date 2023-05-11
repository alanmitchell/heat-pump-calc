import pickle
import gzip
from glob import glob


for f in glob('/home/alan/temp/hpc/*.gz'):
    with gzip.open(f, 'rb') as f:
        cobj = pickle.load(f)

    cobj.df_hourly.to_csv('1683765593.32.df_hourly.csv')
