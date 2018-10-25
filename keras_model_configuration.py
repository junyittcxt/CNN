import keras
# from keras.models import Sequential
# from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D

def cnn_model_conf_1(shape_x):
    model = keras.models.Sequential()
    model.add(keras.layers.Reshape([shape_x[1],shape_x[2],1], input_shape=(shape_x[1],shape_x[2])))
    model.add(keras.layers.Conv2D(128, kernel_size=(15,1), activation='relu'))
    model.add(keras.layers.Conv2D(16, kernel_size=(2,1), activation='relu'))
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(1, activation='sigmoid'))
    return model


def rnn_model_conf_1_best(shape_x):
    model = keras.models.Sequential()
    # model.add(keras.layers.Reshape([shape_x[1]*shape_x[2]], input_shape=(shape_x[1],shape_x[2])))
    model.add(keras.layers.CuDNNLSTM(128, input_shape=(shape_x[1],shape_x[2]), return_sequences = True))
    model.add(keras.layers.CuDNNLSTM(64))
    model.add(keras.layers.Dense(64, activation='relu'))
    model.add(keras.layers.Dropout(0.5))
    model.add(keras.layers.Dense(16, activation='relu'))
    model.add(keras.layers.Dense(4, activation='relu'))
    # model.add(keras.layers.Dense(8, activation='relu'))

    # model.add(keras.layers.CuDNNLSTM(4, input_shape=(shape_x[1],shape_x[2])))


    model.add(keras.layers.Dense(1, activation='sigmoid'))
    return model

def rnn_model_conf_1(shape_x):
    model = keras.models.Sequential()
    # model.add(keras.layers.Reshape([shape_x[1]*shape_x[2]], input_shape=(shape_x[1],shape_x[2])))
    model.add(keras.layers.CuDNNLSTM(128, input_shape=(shape_x[1],shape_x[2]), return_sequences = True))
    model.add(keras.layers.CuDNNLSTM(64))
    model.add(keras.layers.Dense(64, activation='relu'))
    model.add(keras.layers.Dropout(0.7))
    model.add(keras.layers.Dense(16, activation='relu'))
    model.add(keras.layers.Dense(4, activation='relu'))
    # model.add(keras.layers.Dense(8, activation='relu'))

    # model.add(keras.layers.CuDNNLSTM(4, input_shape=(shape_x[1],shape_x[2])))


    model.add(keras.layers.Dense(1, activation='sigmoid'))
    return model


def multi_cnn_model_conf_1(shape_x, shape_y):
    model = keras.models.Sequential()
    model.add(keras.layers.Reshape([shape_x[1],shape_x[2],1], input_shape=(shape_x[1],shape_x[2])))
    model.add(keras.layers.Conv2D(128, kernel_size=(15,1), activation='relu'))
    model.add(keras.layers.Conv2D(16, kernel_size=(2,1), activation='relu'))
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(shape_y[1], activation='sigmoid'))
    return model

def multi_rnn_model_conf_1(shape_x, shape_y):
    model = keras.models.Sequential()
    # model.add(keras.layers.CuDNNLSTM(32, input_shape=(shape_x[1],shape_x[2]), return_sequences = True))
    model.add(keras.layers.CuDNNLSTM(32, input_shape=(shape_x[1],shape_x[2])))
    # model.add(keras.layers.CuDNNLSTM(64))
    model.add(keras.layers.Dense(32, activation='relu'))
    model.add(keras.layers.Dropout(0.7))
    model.add(keras.layers.Dense(16, activation='relu'))
    model.add(keras.layers.Dense(shape_y[1], activation='sigmoid'))
    return model
