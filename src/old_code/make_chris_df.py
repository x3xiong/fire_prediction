import cPickle
import sys

import numpy as np
import pandas as pd

from geometry.grid_conversion import ak_bb
from geometry.grid_conversion import get_gfs_val
from carpentry.get_modis_data import append_xy
from util.daymonth import monthday2day


def add_daymonth(df):
    days = map(lambda x,y,z: monthday2day(x,y,leapyear=(z%4)), df.month, df.day, df.year)
    df.loc[:,'dayofyear'] = days
    return df


def get_feat_df(year, outfile=None, fire_df_loc='/extra/zbutler0/data/west_coast.pkl',
                gfs_locs=('/extra/zbutler0/data/temp_dict.pkl', '/extra/zbutler0/data/hum_dict.pkl',
                          '/extra/zbutler0/data/vpd_dict.pkl'),
                gfs_names=('temp','humidity','vpd'), clust_thresh=10):
    with open(fire_df_loc) as ffire:
        fire_df = cPickle.load(ffire)
    fire_df = fire_df[fire_df.year == year]
    if "dayofyear" not in fire_df:
        fire_df = add_daymonth(fire_df)
    # If no XYs, create them, assuming we're in Alaska
    if "x" not in fire_df:
        fire_df = append_xy(fire_df, ak_bb)

    gfs_dict_dict = dict()
    for loc,name in zip(gfs_locs, gfs_names):
        with open(loc) as fpkl:
            gfs_dict_dict[name] = cPickle.load(fpkl)

    gfs_vecs = dict()
    for name, gfs_dict in gfs_dict_dict.iteritems():
        gfs_vecs[name] = np.zeros(len(fire_df)) + np.nan

    for i,fire_event in enumerate(fire_df.index):
        for name, gfs_dict in gfs_dict_dict.iteritems():
            try:
                lat = fire_df.lat[fire_event]
                lon = fire_df.long[fire_event]
                day = fire_df.day[fire_event]
                month = fire_df.month[fire_event]
                gfs_vecs[name][i] = get_gfs_val(lat, lon, day, month, gfs_dict, year)
            except KeyError as e:
                pass
            except IndexError as e:
                pass
    for name, vec in gfs_vecs.iteritems():
        fire_df[name] = pd.Series(vec, index=fire_df.index)

    if outfile:
        with open(outfile,'w') as fout:
            cPickle.dump(fire_df, fout, cPickle.HIGHEST_PROTOCOL)
    return fire_df


def get_multiple_feat_dfs(first_year, last_year, base_file_name):
    for year in xrange(first_year, last_year+1):
        get_feat_df(year, base_file_name + "_%d.pkl" % year)


def to_csv(basename, outname):
    df_arr = []
    for year in xrange(2010,2017):
        with open('%s_%d.pkl' % (basename, year)) as fpkl:
            df = cPickle.load(fpkl)
            df['year'] = pd.Series(np.zeros(len(df)) + year, index=df.index)
            df_arr.append(df)
    big_df = pd.concat(df_arr)
    big_df.to_csv(outname)


if __name__ == "__main__":
    get_multiple_feat_dfs(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
    to_csv(sys.argv[3], sys.argv[3] + ".csv")

