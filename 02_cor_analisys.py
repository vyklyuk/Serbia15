import glob
import pandas as pd
folder='corr'

def lag_analisys(file):
    df=pd.read_excel(file, index_col=0)
    cor = df.max()
    lag = df.idxmax()
    f = file[file.find("/")+1:file.find("_corr")]
    cor.name = lag.name = f
    return cor, lag

def lag_choice(folder, file_type):
    files_max = glob.glob(folder+"/*"+file_type+".xlsx")
    df_c = pd.DataFrame()
    df_l = pd.DataFrame()
    for file in files_max:
        print(file)
        c,l = lag_analisys(file)
        df_c=df_c.join(c, how='outer' )
        df_l=df_l.join(l, how='outer' )
    return df_c, df_l

c, l = lag_choice(folder, 'delta')
writer = pd.ExcelWriter('DataSet_delta_lag.xlsx')
c.to_excel(writer,'correlation')
l.to_excel(writer,'lag')
writer.save()

c, l = lag_choice(folder, 'max')
writer = pd.ExcelWriter('DataSet_max_lag.xlsx')
c.to_excel(writer,'correlation')
l.to_excel(writer,'lag')
writer.save()
