import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
# from keras.models import Sequential
# from keras.layers import Dense
# from keras.layers import LSTM
# from keras.layers import Dropout
# from keras.callbacks import EarlyStopping
from sklearn.metrics import mean_squared_error
from sklearn import linear_model
from sklearn.model_selection import cross_val_predict, cross_validate
from sklearn.model_selection import KFold
# from keras.layers.convolutional import Conv1D, Conv2D
# from keras.layers.convolutional import MaxPooling1D, MaxPooling2D
# from keras.layers import Flatten
# from keras import regularizers


def interpolate(ds, method='time'):
    """
    Інтерполяція DataFrame з відріззанням хвостів зпереду і ззаду
    :param ds: DataFrame
    :param method: Метод
    :return:
    """

    df = pd.DataFrame()
    for c in ds.columns:
        ts = ds[c]
        date_begin = ts[~np.isnan(ts)].index[0]
        date_end = ts[~np.isnan(ts)].index[-1]
        # print(c, date_begin, date_end)
        ts = ts[np.logical_and(ts.index >= date_begin, ts.index <= date_end)].interpolate(method=method)
        df = df.join(ts, how='outer')
    return df


def my_plt(dt, plt, col, n, l='', title=''):
    """
    Аналіз графіків
    :param dt: DataFrame
    :param plt: Фігура для виводу
    :param col: перелік індексів полів для виводу графіків
    :param n: Чи знищувати порожні рядки
    :param l: Розташування легенди
    :param title: Назва графіка
    :return:
    """
    font = {'size': 10}
    plt.rc('font', **font)
    plt.subplots_adjust(bottom=0.05)
    x = dt.index
    leg = []
    plt.title(title)
    plt.xlabel('Date')
    for i in col:
        y = dt[dt.columns[i]].values
        if n:
            yn = preprocessing.normalize(y[~np.isnan(y)].reshape(1, -1))
            y[~np.isnan(y)] = yn[0]
        plt.plot(x, y)
        leg = leg + ["%s" % dt.columns[i]]
        # leg=leg+["%s" % dt.columns[i]]
    plt.legend(leg, loc=l)
    plt.xlim(xmin=x[0], xmax=x[-1])
    # plt.xticks(np.arange(0, len(X), 8), [X[i][:2]+'.'+X[i][3:-4] for i in range(0,len(X), 8)], rotation=0)


def lag_correlation_ts(y, x, lag):
    """
    Лагова кореляція для 2 DateSeries
    :param y: fixed
    :param x: shifted
    :param lag:
    :return:
    """
    r = [0] * (lag + 1)
    y = y.copy()
    x = x.copy()
    y.name = "y"
    x.name = "x"

    for i in range(0, lag + 1):
        ds = y.copy().to_frame()
        ds = ds.join(x.shift(i), how='outer')
        r[i] = ds.corr().values[0][1]
    return r


def lag_correlation(df_x, df_y, lag=10, file=None):
    """
    Лагова перевірка
    :param df_x: DataFrame вхідних полів
    :param df_y: DataFrame вихідних полів
    :param lag: перевірочнй лаг
    :param file: файл виводу результатів
    :return:
    """
    if file is not None:
        print(file)
        writer = pd.ExcelWriter(file)
        for s in df_y.columns:
            l = pd.DataFrame()
            for x in df_x.columns:
                c = lag_correlation_ts(df_y[s], df_x[x], lag)
                df_c = pd.DataFrame(c)
                df_c.columns = [x]
                l = l.join(df_c, how='outer')
            l.to_excel(writer, s)
        writer.save()
    else:
        print("No file")
    return None


def series_to_supervised(in_data, tar_data, n_in=1, dropnan=True, target_dep=False):
    """
    Перетворення до навчальної вибірки з врахуванням лагу
    :param in_data: Вхідні поля
    :param tar_data: Вихідне поле (одне)
    :param n_in: Лаговий зсув
    :param dropnan: Чи знищувати порожні рядки
    :param target_dep: Чи враховувати лаг вхідного поля В разі врахування вхідні почнуться з лагу 1
    :return: Навчальну вибірку. Останнє поле - вихідне
    """

    n_vars = in_data.shape[1]
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    # for i in range(n_in, -1, -1):
    if target_dep:
        i_start = 1
    else:
        i_start = 0
    for i in range(i_start, n_in + 1):
        cols.append(in_data.shift(i))
        names += [('%s(t-%d)' % (in_data.columns[j], i)) for j in range(n_vars)]

    if target_dep:
        for i in range(n_in, -1, -1):
            cols.append(tar_data.shift(i))
            names += [('%s(t-%d)' % (tar_data.name, i))]
    else:
        # put it all together
        cols.append(tar_data)
        # print(tar_data.name)
        names.append(tar_data.name)
    agg = pd.concat(cols, axis=1)
    agg.columns = names

    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)

    return agg

def CNN2d_model(train_x, filter=64):
    """
    Згорткова мережа 2d
    :param train_x: навчальна вибірка
    :param neurons: Кількість нейронів
    :return: модель
    """
    # activity_regularizer = regularizers.l2(0.001)
    activity_regularizer = None

    model = Sequential()
    model.add(Conv2D(filter, kernel_size=(5, 1), activity_regularizer=activity_regularizer, activation='relu', input_shape=train_x.shape[1:]))
    model.add(MaxPooling2D(pool_size=(2, 1)))
    model.add(Conv2D(filter, kernel_size=(5, 1), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 1)))
    model.add(Dropout(rate=0.25))

    # model.add(Conv2D(filter, kernel_size=(1, 1), activation='relu'))
    # model.add(Conv2D(filter, kernel_size=(1, 1), activation='relu'))
    # model.add(MaxPooling2D(pool_size=(2, 1)))
    # model.add(Dropout(rate=0.25))
    model.add(Flatten())
    model.add(Dense(int(filter/2), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model


def CNN_model(train_x, filter=64):
    """

    :param train_x: навчальна вибірка
    :param neurons: Кількість нейронів
    :return: модель
    """

    n_features=1
    model = Sequential()
    # activity_regularizer=regularizers.l2(0.001)
    activity_regularizer = None
    model.add(Conv1D(filters=filter, kernel_size=5, activity_regularizer=activity_regularizer, activation='relu', input_shape=(train_x.shape[1], n_features)))
    model.add(Conv1D(filters=filter, kernel_size=5, activation='relu' ))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.2))
    # model.add(Conv1D(filters=filter*2, kernel_size=1, activation='relu' ))
    # model.add(Conv1D(filters=filter*2, kernel_size=1, activation='relu' ))
    # model.add(MaxPooling1D(pool_size=1))
    # model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dense(50, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model

def LSTM_model(train_x_lstm, train_y_lstm, neurons=10):
    """
    Побудова LSTM мережі
    :param train_x_lstm:
    :param train_y_lstm:
    :param neurons:
    :return: модель
    """
    multy_layer = True
    # activity_regularizer=regularizers.l2(0.001)
    activity_regularizer = None
    ''' return_sequences=False,, activation='relu', '''
    model = Sequential()
    model.add(LSTM(neurons, return_sequences=multy_layer, activity_regularizer=activity_regularizer, input_shape=(train_x_lstm.shape[1], train_x_lstm.shape[2])))
    model.add(Dropout(0.2))
    if multy_layer:
        model.add(LSTM(neurons))
        model.add(Dropout(0.2))
        # model.add(Dense(neurons, kernel_initializer='normal', activation='relu'))
        # model.add(Dropout(0.2))
    model.add(Dense(train_y_lstm.shape[1]))
    # activation='sigmoid'
    model.compile(loss='mse', optimizer='adam')
    return model


# def LSTM_single_model(DF_X, DF_Y, lag_in=1, train_size=0.7, neurons=10, epochs=400, patience=0, target_dep=False,
#                       only_output=False, verbose=2):
#     """
#     Проста нейроннна мережа
#     :param DF_X: DataFrame вхідних полів
#     :param DF_Y: DataFrame вихідного поля
#     :param lag_in: лаг вхідних полів
#     :param train_size: Розмір навчальної вибірки
#     :param neurons: Кількість нейронів LSTM
#     :param epochs: Кількість епох навчання
#     :param patience: Overfitting
#     :param target_dep: Чи враховувати лаг вхідного поля В разі врахування вхідні почнуться з лагу 1
#     :return: Прогноз нейронної мережі
#     """
#
#     DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
#     if only_output and target_dep:
#         y_LSTM, x_LSTM = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
#     else:
#         y_LSTM, x_LSTM = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
#     # print(x_LSTM.columns)
#
#     scaler_x_LSTM = MinMaxScaler(feature_range=(0, 1))
#     scaler_y_LSTM = MinMaxScaler(feature_range=(0, 1))
#
#     scaled_x_LSTM = scaler_x_LSTM.fit_transform(x_LSTM)
#     scaled_y_LSTM = scaler_y_LSTM.fit_transform(y_LSTM)
#
#     #
#
#     n_obs = int(y_LSTM.shape[0] * train_size)
#     train_x_LSTM, train_y_LSTM = scaled_x_LSTM[:n_obs, :], scaled_y_LSTM[:n_obs, :]
#     test_x_LSTM, test_y_LSTM = scaled_x_LSTM[n_obs:, :], scaled_y_LSTM[n_obs:, :]
#     #
#     if target_dep:
#         resh_x_train = train_x_LSTM.shape[0]
#         resh_y_train = lag_in
#         resh_z_train = 1 + train_x_LSTM.shape[1] // (lag_in + 1)
#         resh_x_test = test_x_LSTM.shape[0]
#         resh_y_test = lag_in
#         resh_z_test = 1 + test_x_LSTM.shape[1] // (lag_in + 1)
#     else:
#         resh_x_train = train_x_LSTM.shape[0]
#         resh_y_train = lag_in + 1
#         resh_z_train = train_x_LSTM.shape[1] // (lag_in + 1)
#         resh_x_test = test_x_LSTM.shape[0]
#         resh_y_test = lag_in + 1
#         resh_z_test = test_x_LSTM.shape[1] // (lag_in + 1)
#
#     train_x_LSTM = train_x_LSTM.reshape((resh_x_train, resh_y_train, resh_z_train))
#     test_x_LSTM = test_x_LSTM.reshape((resh_x_test, resh_y_test, resh_z_test))
#
#     model = LSTM_model(train_x_LSTM, train_y_LSTM, neurons)
#     batch_size = int(train_y_LSTM.shape[0] * .1)
#
#     call = []
#     if patience > 0:
#         reduce_lr = EarlyStopping(monitor='val_loss', patience=10, verbose=0, mode='auto')
#         call.append(reduce_lr)
#     history = model.fit(train_x_LSTM, train_y_LSTM, epochs=epochs, batch_size=batch_size,
#                         validation_data=(test_x_LSTM, test_y_LSTM), verbose=2, shuffle=False, callbacks=call)
#     # print("Пройшло епох", history.epoch[-1]+1)
#     if history.history['val_loss'][-1]  < history.history['loss'][-1]:
#         print("Wrong model for output ", DF_Y.name)
#         print("Train loss", history.history['val_loss'][-1])
#         print("Test loss", history.history['val_loss'][-1])
#
#     forecast_train_LSTM = model.predict(train_x_LSTM)
#     forecast_test_LSTM = model.predict(test_x_LSTM)
#     del model
#
#     forecast_train_LSTM = scaler_y_LSTM.inverse_transform(forecast_train_LSTM)
#
#     forecast = pd.DataFrame(forecast_train_LSTM)
#     forecast.index = y_LSTM.index[:n_obs]
#     forecast.columns = ['Train']
#     res_LSTM = forecast.copy()
#     if train_size < 1:
#         forecast_test_LSTM = scaler_y_LSTM.inverse_transform(forecast_test_LSTM)
#         forecast = pd.DataFrame(forecast_test_LSTM)
#         forecast.index = y_LSTM.index[n_obs:]
#         forecast.columns = ['Test']
#         res_LSTM = res_LSTM.join(forecast, how='outer')
#
#     return res_LSTM


def LSTM_crossvalidation(DF_X, DF_Y, n_splits=10, lag_in=1, neurons=10, epochs=400, patience=0, target_dep=False,
                         only_output=False, shuffle=False, verbose=2):
    """

    :param DF_X:
    :param DF_Y:
    :param n_splits:
    :param lag_in:
    :param neurons:
    :param epochs:
    :param patience:
    :param target_dep:
    :param only_output:
    :param shuffle:
    :param verbose:
    :return:
    """

    DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
    if only_output and target_dep:
        y_LSTM, x_LSTM = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
    else:
        y_LSTM, x_LSTM = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
    # print(x_LSTM.columns)

    scaler_x_LSTM = MinMaxScaler(feature_range=(0, 1))
    scaler_y_LSTM = MinMaxScaler(feature_range=(0, 1))

    scaled_x_LSTM = scaler_x_LSTM.fit_transform(x_LSTM)
    scaled_y_LSTM = scaler_y_LSTM.fit_transform(y_LSTM)

    train_y = scaled_y_LSTM
    if target_dep:
        resh_x_train = scaled_x_LSTM.shape[0]
        resh_y_train = lag_in
        resh_z_train = 1 + scaled_x_LSTM.shape[1] // (lag_in + 1)
    else:
        resh_x_train = scaled_x_LSTM.shape[0]
        resh_y_train = lag_in + 1
        resh_z_train = scaled_x_LSTM.shape[1] // (lag_in + 1)



    train_x_LSTM = scaled_x_LSTM.reshape((resh_x_train, resh_y_train, resh_z_train))

    cw_r_test = np.zeros(train_y.shape)
    cw_r_train = np.zeros(train_y.shape)
    batch_size = int(train_y.shape[0] * .1)
    call = []
    if patience > 0:
        reduce_lr = EarlyStopping(monitor='val_loss', patience=10, verbose=0, mode='auto', restore_best_weights=True)
        call.append(reduce_lr)

    h = []
    wrong_model = 0
    i = 0
    # crossvalidation
    kf = KFold(n_splits=n_splits)
    kf.shuffle=shuffle
    for train_index, test_index in kf.split(train_y):
        i += 1
        # print("TRAIN:", train_index, "TEST:", test_index)
        # print(train_x_LSTM.shape,train_y.shape)
        tr_X = train_x_LSTM[train_index, :, :]
        tr_Y = train_y[train_index]
        ts_X = train_x_LSTM[test_index, :, :]
        ts_Y = train_y[test_index]
        # print(tr_X.shape,tr_Y.shape,ts_X.shape,ts_Y.shape)

        model = LSTM_model(tr_X, tr_Y, neurons)
        history = model.fit(tr_X, tr_Y, epochs=epochs, batch_size=batch_size, validation_data=(ts_X, ts_Y), verbose=0,
                            shuffle=False, callbacks=call)
        h.append(history.epoch[-1])
        yhat_test = model.predict(ts_X)
        yhat_train = model.predict(tr_X)
        mse_test = np.mean((yhat_test - ts_Y) ** 2)
        mse_train = np.mean((yhat_train - tr_Y) ** 2)

        if mse_test < mse_train:
            wrong_model += 1

        if verbose>0:
            if mse_test < mse_train:
                print("#", i, "Wrong LSTM model for output ", DF_Y.name)
                print("Train loss", mse_train)
                print("Test loss", mse_test)
            else:
                print("#", i, "OK LSTM model for output ", DF_Y.name)

        del model
        cw_r_test[test_index] = yhat_test
        cw_r_train[train_index] = yhat_train
    if wrong_model > 0:
        print("Wrong LSTM model for output ", DF_Y.name, wrong_model * 100 // n_splits, "% models wrong")
    else:
        print("OK for all LSTM model")

    forecast_test = scaler_y_LSTM.inverse_transform(cw_r_test)
    forecast_train = scaler_y_LSTM.inverse_transform(cw_r_train)

    res_test = pd.DataFrame(forecast_test)
    res_test.index = y_LSTM.index
    res_test.columns = ['CV_Test_LSTM']

    res_train = pd.DataFrame(forecast_train)
    res_train.index = y_LSTM.index
    res_train.columns = ['CV_Train_LSTM']

    mse_test = np.mean((res_test.values - y_LSTM.values) ** 2)
    mse_train = np.mean((res_train.values - y_LSTM.values) ** 2)
    return res_train, res_test, mse_train, mse_test, h


    #     h.append(history.epoch[-1])
    #     yhat = model.predict(ts_X)
    #     yhat = scaler_y_LSTM.inverse_transform(yhat)
    #     del model
    #     cw_r[test_index] = yhat
    # if wrong_model > 0:
    #     print("Wrong LSTM model for output ", DF_Y.name, wrong_model * 100 / n_splits, "% models wrong")
    #
    # forecast = pd.DataFrame(cw_r)
    # forecast.index = y_LSTM.index
    # forecast.columns = ['CV_Test_LSTM']
    # return forecast, h


# def Linear_single_model(DF_X, DF_Y, lag_in=1, train_size=0.7, target_dep=False, only_output=False):
#     """ Проста лінійна модель
#     # DF_X, DataFrame вхідних полів
#     # DF_Y, DataFrame вихідного поля
#     # lag_in, лаг вхідних полів
#     """
#
#     DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
#
#     if only_output and target_dep:
#         y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
#     else:
#         y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
#     # print(x.columns)
#
#     scaler_x = MinMaxScaler(feature_range=(0, 1))
#     scaler_y = MinMaxScaler(feature_range=(0, 1))
#
#     scaled_x = scaler_x.fit_transform(x)
#     scaled_y = scaler_y.fit_transform(y)
#
#     #
#
#     n_obs = int(y.shape[0] * train_size)
#     train_x, train_y = scaled_x[:n_obs, :], scaled_y[:n_obs, :]
#     test_x, test_y = scaled_x[n_obs:, :], scaled_y[n_obs:, :]
#     #
#
#
#     model = linear_model.LinearRegression()
#     model.fit(train_x, train_y)
#     pr_train = model.predict(train_x)
#
#     if train_size < 1:
#         pr_test = model.predict(test_x)
#         err_train = mean_squared_error(train_y, pr_train)
#         err_test = mean_squared_error(test_y, pr_test)
#         # print("Пройшло епох", history.epoch[-1]+1)
#         if err_test < err_train:
#             print("Wrong model for output ", DF_Y.name)
#             print("Train loss", err_train)
#             print("Test loss", err_test)
#     del model
#
#     forecast_train = scaler_y.inverse_transform(pr_train)
#
#     forecast = pd.DataFrame(forecast_train)
#     forecast.index = y.index[:n_obs]
#     forecast.columns = ['Train']
#     res = forecast.copy()
#     if train_size < 1:
#         forecast_test = scaler_y.inverse_transform(pr_test)
#         forecast = pd.DataFrame(forecast_test)
#         forecast.index = y.index[n_obs:]
#         forecast.columns = ['Test']
#         res = res.join(forecast, how='outer')
#
#     return res


def Linear_crossvalidation(DF_X, DF_Y, lag_in=1, n_splits=10, target_dep=False, only_output=False, shuffle=False, verbose=2):
    """

    :param DF_X: DataFrame вхідних полів
    :param DF_Y: DataFrame вихідного поля
    :param lag_in: лаг вхідних полів
    :param n_splits: Кількіть розділень
    :param target_dep: врахування вихідного поля
    :param only_output: тільки вихідне поле як вхідні параметри
    :param shuffle: Чи перемішувати кросвалідацію
    :return: прогноз навчальної вибірки, прогноз тренувальної вибірки, MSE навчальної вибірки, MSE тренувальної вибірки
    """


    DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
    if only_output and target_dep:
        y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
    else:
        y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
    # print(x.columns)

    # print("Input: ", x.columns)
    # print("Output:", y.columns)
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))

    scaled_x = scaler_x.fit_transform(x)
    scaled_y = scaler_y.fit_transform(y)

    kf = KFold(n_splits=n_splits)
    kf.shuffle=shuffle
    i = 0

    cw_r_test = np.zeros(scaled_y.shape)
    cw_r_train = np.zeros(scaled_y.shape)
    wrong_model = 0
    for train_index, test_index in kf.split(scaled_y):
        i += 1
        tr_X = scaled_x[train_index, :]
        tr_Y = scaled_y[train_index]
        ts_X = scaled_x[test_index, :]
        ts_Y = scaled_y[test_index]
        # print(tr_X.shape,tr_Y.shape,ts_X.shape,ts_Y.shape)
        # exit()
        model = linear_model.LinearRegression()
        model.fit(tr_X, tr_Y)
        yhat_test = model.predict(ts_X)
        yhat_train = model.predict(tr_X)
        mse_test=np.mean((yhat_test - ts_Y) ** 2)
        mse_train=np.mean((yhat_train - tr_Y) ** 2)
        del model

        if mse_test < mse_train:
            wrong_model += 1

        if verbose>0:
            if mse_test < mse_train:
                print("#", i, "Wrong Linear model for output ", DF_Y.name)
                print("Train loss", mse_train)
                print("Test loss", mse_test)
            else:
                print("#", i, "OK Linear model for output ", DF_Y.name)

        cw_r_test[test_index] = yhat_test
        cw_r_train[train_index] = yhat_train
    if wrong_model > 0:
        print("Wrong Linear model for output ", DF_Y.name, wrong_model * 100 // n_splits, "% models wrong")
    else:
        print("OK for all Linear model")

    forecast_test = scaler_y.inverse_transform(cw_r_test)
    forecast_train = scaler_y.inverse_transform(cw_r_train)

    res_test = pd.DataFrame(forecast_test)
    res_test.index = y.index
    res_test.columns = ['CV_Test_Linear']

    res_train = pd.DataFrame(forecast_train)
    res_train.index = y.index
    res_train.columns = ['CV_Train_Linear']

    mse_test = np.mean((res_test.values - y.values) ** 2)
    mse_train = np.mean((res_train.values - y.values) ** 2)
    return res_train, res_test, mse_train, mse_test


# def SVR_crossvalidation(DF_X, DF_Y, lag_in=1, n_splits=10, target_dep=False, only_output=False, shuffle=False, verbose=2):
#     """ Проста лінійна модель
#     # DF_X, DataFrame вхідних полів
#     # DF_Y, DataFrame вихідного поля
#     # lag_in, лаг вхідних полів
#     """
#
#     DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
#     if only_output and target_dep:
#         y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
#     else:
#         y, x = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
#     # print(x.columns)
#
#     # print("Input: ", x.columns)
#     # print("Output:", y.columns)
#     scaler_x = MinMaxScaler(feature_range=(0, 1))
#     scaler_y = MinMaxScaler(feature_range=(0, 1))
#
#     scaled_x = scaler_x.fit_transform(x)
#     scaled_y = scaler_y.fit_transform(y.values.reshape(-1, 1))
#
#     from sklearn.svm import SVR
#     # model  = SVR(kernel='linear', C=1e3)
#     # model = SVR(kernel='poly', C=1e3, degree=2)
#     model = SVR(kernel='rbf', C=1e3, gamma=0.1)
#     kf = KFold(n_splits=n_splits)
#     kf.shuffle=shuffle
#     predicted = cross_val_predict(model, scaled_x, scaled_y.ravel(), cv=n_splits)
#     scores = cross_validate(model, scaled_x, scaled_y.ravel(), cv=kf,
#                             scoring=('neg_mean_squared_error'),
#                             return_train_score=True)
#     err_train = np.array(scores['train_score'])*(-1)
#     err_test = np.array(scores['test_score'])*(-1)
#     if np.sum(err_test < err_train) > 0:
#         print("Wrong SRV model for output ", DF_Y.name, np.sum(err_test < err_train) * 100 // n_splits, "% models wrong")
#         print("Train loss", err_train)
#         print("Test loss", err_test)
#         print("Errors loss", err_test < err_train)
#     del model
#     # print("Predicted", predicted.shape)
#     forecast_train = scaler_y.inverse_transform(predicted.reshape(-1 , 1))
#
#     forecast = pd.DataFrame(forecast_train)
#     forecast.index = y.index
#     forecast.columns = ['CV_Test_SVR']
#     res = forecast.copy()
#
#     return res


def CNN1D_crossvalidation(DF_X, DF_Y, n_splits=10, lag_in=2, filter=64, epochs=400, patience=0, target_dep=False,
                         only_output=False, shuffle=False, verbose=2):
    """

    :param DF_X: DataSet входів
    :param DF_Y: DataSet входів
    :param n_splits: кількість розбиттів
    :param lag_in: Величина лагу
    :param neurons: кількість нейронів
    :param epochs: максимальна кількість епох
    :param patience: коли зупинити навчання
    :param target_dep: чи врховувати історію вихідного поля
    :param only_output: тільки вихідна поле на вхід
    :param shuffle: чи мішати кросвалідаційну вибірку
    :return:
    """
    DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
    if only_output and target_dep:
        y_CNN, x_CNN = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
    else:
        y_CNN, x_CNN = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
    # print(x_CNN.columns)

    scaler_x_CNN = MinMaxScaler(feature_range=(0, 1))
    scaler_y_CNN = MinMaxScaler(feature_range=(0, 1))

    scaled_x_CNN = scaler_x_CNN.fit_transform(x_CNN)
    scaled_y_CNN = scaler_y_CNN.fit_transform(y_CNN)


    train_y = scaled_y_CNN
    train_x_CNN = scaled_x_CNN
    train_x_CNN = train_x_CNN.reshape((train_x_CNN.shape[0], train_x_CNN.shape[1], 1))

    cw_r_test = np.zeros(train_y.shape)
    cw_r_train = np.zeros(train_y.shape)
    batch_size = int(train_y.shape[0] * .1)
    call = []
    if patience > 0:
        reduce_lr = EarlyStopping(monitor='val_loss', patience=10, verbose=0, mode='auto', restore_best_weights=True)
        call.append(reduce_lr)

    h = []
    wrong_model = 0
    i = 0
    # crossvalidation
    kf = KFold(n_splits=n_splits)
    kf.shuffle=shuffle
    for train_index, test_index in kf.split(train_y):
        i += 1
        tr_X = train_x_CNN[train_index, :]
        tr_Y = train_y[train_index]
        ts_X = train_x_CNN[test_index, :]
        ts_Y = train_y[test_index]
        # print(tr_X.shape,tr_Y.shape,ts_X.shape,ts_Y.shape)
        # exit()
        model = CNN_model(tr_X, filter)
        history = model.fit(tr_X, tr_Y, epochs=epochs, batch_size=batch_size, validation_data=(ts_X, ts_Y), verbose=0,
                            shuffle=False, callbacks=call)
        # if history.history['val_loss'][-1] < history.history['loss'][-1]:
        #     print("!#", i, "Wrong model  for output ", DF_Y.name)
        #     print("Train loss", history.history['loss'][-1])
        #     print("Test loss", history.history['val_loss'][-1])
        #     wrong_model += 1
        # else:
        #     print("#", i, "OK model  for output ", DF_Y.name)

        h.append(history.epoch[-1])
        yhat_test = model.predict(ts_X)
        yhat_train = model.predict(tr_X)
        mse_test=np.mean((yhat_test - ts_Y) ** 2)
        mse_train=np.mean((yhat_train - tr_Y) ** 2)
        if mse_test < mse_train:
            wrong_model += 1

        if verbose>0:
            if mse_test < mse_train:
                print("#", i, "Wrong CNN1D model for output ", DF_Y.name)
                print("Train loss", mse_train)
                print("Test loss", mse_test)
            else:
                print("#", i, "OK CNN1D model for output ", DF_Y.name)

        del model
        cw_r_test[test_index] = yhat_test
        cw_r_train[train_index] = yhat_train
    if wrong_model > 0:
        print("Wrong CNN1D model for output ", DF_Y.name, wrong_model * 100 // n_splits, "% models wrong")
    else:
        print("OK for all CNN1D model")

    forecast_test = scaler_y_CNN.inverse_transform(cw_r_test)
    forecast_train = scaler_y_CNN.inverse_transform(cw_r_train)

    res_test = pd.DataFrame(forecast_test)
    res_test.index = y_CNN.index
    res_test.columns = ['CV_Test_CNN1D']

    res_train = pd.DataFrame(forecast_train)
    res_train.index = y_CNN.index
    res_train.columns = ['CV_Train_CNN1D']

    mse_test = np.mean((res_test.values - y_CNN.values) ** 2)
    mse_train = np.mean((res_train.values - y_CNN.values) ** 2)
    return res_train, res_test, mse_train, mse_test, h


def CNN2D_crossvalidation(DF_X, DF_Y, n_splits=10, lag_in=1, filter=10, epochs=400, patience=0, target_dep=False,
                         only_output=False, shuffle=False, verbose=2):
    """

    :param DF_X:
    :param DF_Y:
    :param n_splits:
    :param lag_in:
    :param filter:
    :param epochs:
    :param patience:
    :param target_dep:
    :param only_output:
    :param shuffle:
    :param verbose:
    :return:
    """

    DF_SV = series_to_supervised(DF_X, DF_Y, lag_in, target_dep=target_dep)
    if only_output and target_dep:
        y_CNN, x_CNN = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[-(lag_in + 1):-1]]
    else:
        y_CNN, x_CNN = DF_SV[DF_SV.columns[-1:]], DF_SV[DF_SV.columns[:-1]]
    # print(x_CNN.columns)

    scaler_x_CNN = MinMaxScaler(feature_range=(0, 1))
    scaler_y_CNN = MinMaxScaler(feature_range=(0, 1))

    scaled_x_CNN = scaler_x_CNN.fit_transform(x_CNN)
    scaled_y_CNN = scaler_y_CNN.fit_transform(y_CNN)

    train_y = scaled_y_CNN
    if target_dep:
        resh_x_train = scaled_x_CNN.shape[0]
        resh_y_train = lag_in
        resh_z_train = 1 + scaled_x_CNN.shape[1] // (lag_in + 1)
    else:
        resh_x_train = scaled_x_CNN.shape[0]
        resh_y_train = lag_in + 1
        resh_z_train = scaled_x_CNN.shape[1] // (lag_in + 1)


    train_x_CNN = scaled_x_CNN.reshape((resh_x_train, resh_y_train, resh_z_train, 1))


    cw_r_test = np.zeros(train_y.shape)
    cw_r_train = np.zeros(train_y.shape)
    batch_size = int(train_y.shape[0] * .1)
    call = []
    if patience > 0:
        reduce_lr = EarlyStopping(monitor='val_loss', patience=10, verbose=0, mode='auto', restore_best_weights=True)
        call.append(reduce_lr)

    h = []
    wrong_model = 0
    i = 0
    # crossvalidation
    kf = KFold(n_splits=n_splits)
    kf.shuffle=shuffle
    for train_index, test_index in kf.split(train_y):
        i += 1
        # print("TRAIN:", train_index, "TEST:", test_index)
        # print(train_x_CNN.shape,train_y.shape)
        tr_X = train_x_CNN[train_index, :, :, :]
        tr_Y = train_y[train_index]
        ts_X = train_x_CNN[test_index, :, :, :]
        ts_Y = train_y[test_index]
        # print(tr_X.shape,tr_Y.shape,ts_X.shape,ts_Y.shape)

        # model = CNN_model(tr_X, tr_Y, neurons)
        model = CNN2d_model(tr_X, filter)
        history = model.fit(tr_X, tr_Y, epochs=epochs, batch_size=batch_size, validation_data=(ts_X, ts_Y), verbose=0,
                            shuffle=False, callbacks=call)
        # if history.history['val_loss'][-1] < history.history['loss'][-1]:
        #     print("#", i, "Wrong model  for output ", DF_Y.name)
        #     print("Train loss", history.history['loss'][-1])
        #     print("Test loss", history.history['val_loss'][-1])
        #     wrong_model += 1
        # else:
        #     print("#", i, "OK model  for output ", DF_Y.name)
        h.append(history.epoch[-1])
        yhat_test = model.predict(ts_X)
        yhat_train = model.predict(tr_X)
        mse_test = np.mean((yhat_test - ts_Y) ** 2)
        mse_train = np.mean((yhat_train - tr_Y) ** 2)

        if mse_test < mse_train:
            wrong_model += 1

        if verbose>0:
            if mse_test < mse_train:
                print("#", i, "Wrong CNN2D model for output ", DF_Y.name)
                print("Train loss", mse_train)
                print("Test loss", mse_test)
            else:
                print("#", i, "OK CNN2D model for output ", DF_Y.name)

        del model
        cw_r_test[test_index] = yhat_test
        cw_r_train[train_index] = yhat_train
    if wrong_model > 0:
        print("Wrong CNN2D model for output ", DF_Y.name, wrong_model * 100 // n_splits, "% models wrong")
    else:
        print("OK for all CNN2D model")

    forecast_test = scaler_y_CNN.inverse_transform(cw_r_test)
    forecast_train = scaler_y_CNN.inverse_transform(cw_r_train)

    res_test = pd.DataFrame(forecast_test)
    res_test.index = y_CNN.index
    res_test.columns = ['CV_Test_CNN2D']

    res_train = pd.DataFrame(forecast_train)
    res_train.index = y_CNN.index
    res_train.columns = ['CV_Train_CNN2D']

    mse_test = np.mean((res_test.values - y_CNN.values) ** 2)
    mse_train = np.mean((res_train.values - y_CNN.values) ** 2)
    return res_train, res_test, mse_train, mse_test, h

