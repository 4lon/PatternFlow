import tensorflow as tf
import os
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np

dataset_prefix = "/home/tomdx/datasets/keras_png_slices_data/"
train_suffix = "keras_png_slices_train"
test_suffix = "keras_png_slices_test"


batch_size = 64
img_height = 256
img_width = 256

def get_data():

    train = []
    test = []
    for root_name, dir_names, file_names in os.walk(dataset_prefix + train_suffix):
        file_names.sort()
        for file_name in file_names:
            img = img_to_array(load_img(root_name + "/" + file_name, color_mode="grayscale"))
            train.append(img)

    for root_name, dir_names, file_names in os.walk(dataset_prefix + test_suffix):
        file_names.sort()
        for file_name in file_names:
            img = img_to_array(load_img(root_name + "/" + file_name, color_mode="grayscale"))
            test.append(img)

    return np.array(train), np.array(test)

train, test = get_data()


