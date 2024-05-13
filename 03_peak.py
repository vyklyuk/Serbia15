import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np

xl = pd.ExcelFile('DataSet.xlsx')
writer = pd.ExcelWriter('Peaks.xlsx')

rem = []
for sh in xl.sheet_names:  # see all sheet names
    if 'delta' in sh:
        DS = pd.read_excel('DataSet.xlsx', sh, index_col=0)
        DS.index = pd.to_datetime(DS.index)
        for i, c in enumerate(DS.columns[:-1]):
            x=DS[c]
            if x.isna().sum() > 3:
                rem.append("Deleted:"+ c + " in " + sh)
                del DS[c]
            # print(c)
            # peaks, _ = find_peaks(x, threshold= (np.max(x)-np.min(x))/10)
            peaks, _ = find_peaks(x)
            # plt.figure(i+1)
            # plt.title(c)
            # plt.plot(x)
            # plt.plot(x.iloc[peaks], "x")
            # plt.savefig(c)

            x.iloc[peaks]=1
            x[x.values!=1]=0
            # print(peaks, c)
        # plt.plot(np.zeros_like(x), "--", color="gray")
        # plt.show()
        DS[DS.columns[-1]] = DS[DS.columns[-1]].apply(lambda x: 0 if x != 0 else 1)
        DS.to_excel(writer, sh )
print(rem)
writer.save()