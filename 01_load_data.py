import pandas as pd
from datetime import datetime
import numpy as np
from data_analysis import lag_correlation
from openpyxl import load_workbook
import glob
import os

def parse(df, col):
    # c_et = ['year', 'day', 'time']
    # for i, c in enumerate(col):
    #     df = df.rename(columns={c: c_et[i]})

    df[col] = df[col].astype("int")
    # df['h'] = df[c_et[-1]] // 100
    # df['m'] = df[c_et[-1]] % 100
    # print(df[col[:-1] + ['h', 'm']])
    df["Date-Time"] = pd.to_datetime(df[col[0]], format='%Y')
    df["Date-Time"] =df["Date-Time"] + (df[col[1]]-1).astype('timedelta64[D]')+(df[col[2]]).astype('timedelta64[h]')
    # df["Date-Time"] = pd.to_datetime(df[col[:-1] + ['h', 'm']])
    df = df.set_index(df['Date-Time'])
    df.index.name = 'date'
    return df.drop(columns=col + ['Date-Time'])

def parse3(df, col):
    df = df.set_index(pd.to_datetime(df[col[0]].astype('str') +" " + df[col[1]].astype('str')))
    df.index.name = 'date'
    return df.drop(columns=col)
    #print(x, x.split(), z, h, m, z+" "+str(h)+" "+str(m))
    # return datetime.strptime(x, '%Y %m %d')
#
# def parse3(x):
#     return datetime.strptime(x, '%Y %m %d %H:%M:%S')

def custom_resampler(arraylike):
    # print(arraylike)
    arraylike = arraylike[~np.isnan(arraylike)]
    arraylike = np.sort(arraylike)
    arraylike = np.trim_zeros(arraylike)
    # print(arraylike)
    if len(arraylike)>=2:
        return (np.max(arraylike) - np.min(arraylike))/np.min(arraylike)
        # return np.min(arraylike)
    elif len(arraylike)==1:
        return arraylike[0]
    else:
        return np.NaN




def pre_prep(file, file_p):

    dt_IPF=pd.read_excel(file,usecols='A:V', skiprows=19).dropna()
    dt_IPF.drop(index=dt_IPF.index[-1],
            axis=0,
            inplace=True)
    dt_IPF = parse(dt_IPF, ['year', 'day', 'hr'])
    dt_IPF[dt_IPF.le(-99)] = np.NaN
    #

    try:
        dt_IPF_cus=dt_IPF.resample('D').apply(custom_resampler)
        dt_IPF_mn = dt_IPF.resample('D').mean()
        dt_IPF=dt_IPF.resample('D').max()

    except:
        dt_IPF_cus = dt_IPF.resample('D').apply(custom_resampler)
        dt_IPF_mn = dt_IPF.resample('D').mean()
        dt_IPF = dt_IPF.resample('D').max()

    #
    # dt_DF=pd.read_excel(file,usecols='N, O, P, Q, U, V, X, Y, Z, AB', skiprows=17).dropna()
    # dt_DF = parse(dt_DF, ['year.1', 'month.1', 'date', 'time.1'])
    # dt_DF[dt_DF.le(-9999)] = np.NaN
    # dt_DF_cus=dt_DF.resample('D').apply(custom_resampler).interpolate(method='pchip')
    # dt_DF=dt_DF.resample('D').max().interpolate(method='pchip')
    # # print(dt_DF)
    # #
    # dt_SW=pd.read_excel(file,usecols='AI, AJ, AK, AL, AP, AQ, AR', skiprows=17).dropna()
    # dt_SW = parse(dt_SW, ['year.2', 'month.2', 'date.1', 'time.2'])
    # dt_SW[dt_SW.le(-9999)] = np.NaN
    # dt_SW_cus=dt_SW.resample('D').apply(custom_resampler).interpolate(method='pchip')
    # dt_SW=dt_SW.resample('D').max().interpolate(method='pchip')
    # # print(dt_SW)
    # #
    dt_RF = pd.read_excel(file,usecols='Y:AA', skiprows=19).dropna()
    dt_RF = parse3(dt_RF, ['DATE', 'TIME'])
    dt_RF[dt_RF.le(-99)] = np.NaN
    dt_RF_mn = dt_RF.resample('D').mean().interpolate(method='pchip')
    dt_RF = dt_RF.resample('D').max().interpolate(method='pchip')
    dt_RF_cus = dt_RF
    # print(dt_RF.shape)
    # #
    dt_FL = pd.read_csv(file_p)
    dt_FL.columns = ['days from the beginning of the flood', 'precipitations']
    dt_FL[dt_FL.columns[0]] = dt_FL[dt_FL.columns[0]] - 13
    dt_FL_cus = dt_FL
    dt_FL_mn = dt_FL
    # print(dt_FL)
    #
    # #
    DS = dt_IPF.copy()
    # DS=DS.join(dt_DF, how='outer' )
    # DS=DS.join(dt_SW, how='outer' )
    DS=DS.join(dt_RF, how='outer' )
    DS[dt_FL.columns[1]] = dt_FL[dt_FL.columns[1]].values
    DS[dt_FL.columns[0]] = dt_FL[dt_FL.columns[0]].values
    #

    DS_mn = dt_IPF_mn.copy()
    DS_mn=DS_mn.join(dt_RF_mn, how='outer' )
    DS_mn[dt_FL_mn.columns[1]] = dt_FL_mn[dt_FL_mn.columns[1]].values
    DS_mn[dt_FL_mn.columns[0]] = dt_FL_mn[dt_FL_mn.columns[0]].values

    # #
    DS_cus = dt_IPF_cus.copy()
    # DS_cus=DS_cus.join(dt_DF_cus, how='outer' )
    # DS_cus=DS_cus.join(dt_SW_cus, how='outer' )
    DS_cus=DS_cus.join(dt_RF_cus, how='outer' )
    DS_cus[dt_FL_cus.columns[1]] = dt_FL_cus[dt_FL_cus.columns[1]].values
    DS_cus[dt_FL_cus.columns[0]] = dt_FL_cus[dt_FL_cus.columns[0]].values
    #
    # #
    # print(DS)
    b = file.rfind('/')
    e = file.rfind('.')
    shit = file[b + 1:e]
    # print(shit)
    try:
        book = load_workbook('DataSet.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('DataSet.xlsx')
    try:
        writer.book = book
    except:
        pass

    DS.to_excel(writer,shit+'_max')
    DS_cus.to_excel(writer,shit+'_delta')
    DS_mn.to_excel(writer,shit+'_mean')

    # if 'DE2 ' in DS.columns:
    #     print("+++++++++++++++++++++++++++++", shit)
    writer.save()
    #
    #
    lag_correlation(DS[DS.columns[:-2]], DS[DS.columns[-2:-1]], lag=11, file='corr/'+shit+'_corr_max.xlsx')
    lag_correlation(DS_cus[DS_cus.columns[:-2]], DS[DS_cus.columns[-2:-1]], lag=11, file='corr/'+shit+'_corr_delta.xlsx')

directory = 'Sun activity'
files = glob.glob(directory + "/*.xlsx")
directory_p = 'Precipitations'
files_p = glob.glob(directory_p+"/*.csv")

# print(files)
# print(files_p)

# files = glob.glob(folder+"/*.xlsx")
# folders = [x[0] for x in os.walk(directory)]

# pre_prep('Sun activity/2010_0275_UKR_NEW.xlsx', 'Precipitations/2010-0275-UKR-padavine.csv')
#
for file in files:
    print(file)
    b = file.rfind('/')
    e = file.rfind('_NEW')
    f = file[b+1:e].replace("_","-")
    pre_prep(file, [i for i in files_p if f in i][0])