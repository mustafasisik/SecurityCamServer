from keras.models import load_model
from glob2 import glob
from keras import preprocessing
import matplotlib.pyplot as plt
import numpy as np
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers.core import Activation, Dropout, Flatten, Dense
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import Adam

class_names = ["safe", "suspicious"]
safes = []
suspicious = []
width = 96
height = 96
for path in glob('media/safe*.*'):
    print("SAF: ", path)
    image = preprocessing.image.load_img(path, target_size=((width, height)))
    im = preprocessing.image.img_to_array(image)
    safes.append(im)

for path in glob('media/suspicious*.*'):
    print("SUS: ", path)
    image = preprocessing.image.load_img(path, target_size=((width, height)))
    im = preprocessing.image.img_to_array(image)
    suspicious.append(im)

safe_type = np.array(safes)
suspicious_type = np.array(suspicious)

x = np.concatenate((safe_type, suspicious_type), axis=0)
y_safe = [0 for item in enumerate(safe_type)]
y_suspicious = [1 for item in enumerate(suspicious_type)]
y = np.concatenate((y_safe, y_suspicious), axis=0)
y = to_categorical(y, num_classes=len(class_names))

conv_1 = 16
conv_1_drop = 0.2
conv_2 = 32
conv_2_drop = 0.2
dense_1_n = 1024
dense_1_drop = 0.2
dense_2_n = 512
dense_2_drop = 0.2
lr = 0.001

epochs = 30
batch_size = 32
color_channels = 3


def build_model(conv_1_drop=conv_1_drop, conv_2_drop=conv_2_drop,
                dense_1_n=dense_1_n, dense_1_drop=dense_1_drop,
                dense_2_n=dense_2_n, dense_2_drop=dense_2_drop,
                lr=lr):
    model = Sequential()
    model.add(Convolution2D(conv_1, (3, 3),
                            input_shape=(width, height, color_channels),
                            activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(conv_1_drop))

    model.add(Convolution2D(conv_2, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(conv_2_drop))

    model.add(Flatten())

    model.add(Dense(dense_1_n, activation='relu'))
    model.add(Dropout(dense_1_drop))

    model.add(Dense(dense_2_n, activation='relu'))
    model.add(Dropout(dense_2_drop))

    model.add(Dense(len(class_names), activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=lr))

    return model



np.random.seed()

model = build_model()

model.fit(x, y, epochs=epochs)

model_json = model.to_json()
with open("model.json", "w") as json_file:
    json_file.write(model_json)
# serialize weights to HDF5
model.save_weights("model.h5")
print("Saved model to disk")