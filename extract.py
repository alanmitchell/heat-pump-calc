# Creates a CSV file for the hourly results of all Calculator runs found in the
# /home/alan/temp/hpc directory.
import pickle
import gzip
from pathlib import Path

base_dir = Path('/home/alan/temp/hpc')
for f in base_dir.glob('*.gz'):
    with gzip.open(f, 'rb') as gzf:
        cobj = pickle.load(gzf)
    print(f.stem, cobj.bldg_name)

    cobj.df_hourly.to_csv(base_dir / f'{f.stem}.df_hourly.csv')
