import pickle
import gzip
from glob import glob


for fn in glob('/home/tabb99/temp/hpc/*.gz'):
    with gzip.open(fn, 'rb') as f:
        cobj = pickle.load(f)
    print(fn)
    base_fn = fn.split('/')[-1]
    base_fn = '.'.join(base_fn.split('.')[:2])
    cobj.df_hourly.to_csv(f'{base_fn}.df_hourly.csv')
