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
