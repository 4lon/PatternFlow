import keras.utils.data_utils
import numpy as np
from matplotlib import pyplot as plt
from nibabel.brikhead import filepath
from skimage.io import imread
from skimage.transform import resize
import math
import nibabel as nib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
# from keras.utils import Sequence
import tensorflow.keras.utils
from keras.models import Sequential
import os
import sys

import unet_model as mdl
import driver as drv





# todo need to input X_set, y_set whish are x_
class ProstateSequence(keras.utils.Sequence):
    # https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly
    # https://towardsdatascience.com/keras-data-generators-and-how-to-use-them-b69129ed779c
    """Data generator"""
    def __init__(self, x_set, y_set, batch_size=1):
    # def __init__(self, x_set, y_set, batch_size=1, dim=(256, 256, 128), n_channels=1,
    #              n_classes=6, shuffle=False):
        """
        :param x_set:
        :param y_set:
        :param batch_size:
        :param dim:
        :param n_channels:
        :param n_classes:
        :param shuffle:
        """
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size
        self.dim = (256,256,128)
        self.n_channels = 1
        self.n_classes = 6
        self.shuffle = False
        self.on_epoch_end()

    def __len__(self):
        """Number of batches per epoch"""
        return math.ceil(len(self.x) / self.batch_size)

    def __getitem__(self, idx):  #todo setup for shuffle
        # https://www.tensorflow.org/api_docs/python/tf/keras/utils/Sequence
        """
        Gets one batch
        :param idx:
        :return: 1 batch of data and a matching batch of labels
        """
        # # indexes are matched so don't  need this section
        # batch_x = self.x[idx * self.batch_size:(idx + 1) *
        #                                        self.batch_size]
        # batch_y = self.y[idx * self.batch_size:(idx + 1) *
        #                                        self.batch_size]

        # Instead indexes same for train & label, or validate & label, or test & label
        # create tmp list of image/label names for batch
        indexes = self.indexes[idx*self.batch_size:(idx+1)*self.batch_size]
        list_data_tmp = [self.x[k] for k in indexes]
        list_label_tmp = [self.y[k] for k in indexes]
        # generate data
        X = self._generation_x(list_data_tmp)
        y = self._generation_y(list_label_tmp)

        return X, y

        # return np.array([                           #todo setup for nii
        #     resize(imread(file_name), (200, 200))
        #     for file_name in batch_x]), np.array(batch_y)

    def _generation_x(self, list_data_tmp):
        """
        Generates one batch of data, given a list of data file paths/names.
        :param list_data_tmp:
        :return: One batch of nparray of data.
        """
        print("hi L88: ", self.dim) #
        # print(list_data_tmp.type)
        # print(list_data_tmp.dim)
        X = np.empty((self.batch_size, *self.dim))
        # X = np.empty((self.batch_size, *self.dim, self.n_channels))  # not working
        print("L92: ", X.dtype)
        print("X.shape: ", X.shape)
        # k = self.read_nii(list_data_tmp)
        # print("k: ", k.shape)


        for i, id in enumerate(list_data_tmp):
            print("i, id: ", i, id) #
            k = self.read_nii(id) #
            print("k: ", k.shape) #
            X[i, ] = self.read_nii(id)
        return X

    def _generation_y(self, list_label_tmp):
        """
        Generates one batch of labels, given a list of labels file paths/names.
        The labels match the data files from _generation_x()
        :param list_data_tmp:
        :return: One batch of nparray of data.
        """
        y = np.empty((self.batch_size, *self.dim), dtype=int)

        for i, id in enumerate(list_label_tmp):
            y[i, ] = self.read_nii(id)   #todo investigate
        return y


    def read_nii(self, file_path):
        """ Reads and returns nparray data from single .nii image"""
        img = nib.load(file_path)
        img_data = img.get_fdata()
        return img_data



    def on_epoch_end(self):  #todo currently set to false
        'Shuffles indexes at end of each epoch'
        self.indexes = np.arange(len(self.y))
        if self.shuffle:
            np.random.shuffle(self.indexes)

    # todo join _dg_x & _dg_y
    def _data_generation(self, list_IDs_temp):
        'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
        # Initialization
        X = np.empty((self.batch_size, *self.dim, self.n_channels))
        y = np.empty(self.batch_size, dtype=int)

        # Generate data
        for i, ID in enumerate(list_IDs_temp):
            # Store sample
            X[i,] = np.load('data/' + ID + '.npy')

            # Store class
            y[i] = self.labels[ID]
            # label shape (256,256,128) -> (256,256,128,6) <class 'numpy.ndarray'>
        return X, keras.utils.to_categorical(y, num_classes=self.n_classes)



def data_info():
    """ Prints info on original data and labels files via raw_data_info(image).  """
    # data info
    img_mr = (nib.load(drv.X_TRAIN_DIR + '\\Case_004_Week0_LFOV.nii.gz')).get_fdata()
    raw_data_info(img_mr)
    # label info
    img_label = (nib.load(drv.Y_TRAIN_DIR + '\\Case_004_Week0_SEMANTIC_LFOV.nii.gz')).get_fdata()
    raw_data_info(img_label)


def raw_data_info(image):
    """ prints info of provided image. """
    print("image information")
    print(type(image))
    print(image.dtype)
    print(image.shape)
    print(np.amin(image), np.amax(image))
    print()


def slices(img):
    """ takes slices of input image."""
    slice_0 = img[127, :, :]
    slice_1 = img[:, 127, :]
    slice_2 = img[:, :, 63]
    show_slices([slice_0, slice_1, slice_2])


def show_slices(sliced):
    """ Prints slices images to screen."""
    for i in sliced:
        plt.imshow(i.T)
        plt.show()

    # todo put into subplots (if works in pycharm)
    # fig, axes = plt.subplots(1, len(sliced))
    # for i, slice in enumerate(sliced):
    #     axes[i].imshow(slice.T, cmap="gray", origin="lower")


def dim_per_directory():
    """ iterates through data and label directories, checking that dimensions are as expected."""
    print("image_train")
    dim_check(drv.image_train)
    print("image_validate")
    dim_check(drv.image_validate)
    print("image_test")
    dim_check(drv.image_test)
    print("label_train")
    dim_check(drv.label_train)
    print("label_validate")
    dim_check(drv.label_validate)
    print("label_test")
    dim_check(drv.label_test)


def dim_check(filepath):
    """ Expected dim of each image and label is (256,256,128)
    Case_019_week1 has dimensions (256,256,144)
    :param filepath:
    :return: None
    """
    for i in filepath:
        tups = read_nii(i).shape
        x, y, z = tups
        if x != 256:
            print("flag x: ", i, x)
        if y != 256:
            print("flag y: ", i, y)
        if z != 128:
            print("flag z: ", i, z)


def min_max_value(file_path):
    """ Return min and max voxel value of all images in file path"""
    min_value = 1000
    max_value = 0
    for i in file_path:
        maxv = np.amax(read_nii(i))
        minv = np.amin(read_nii(i))
        if maxv > max_value:
            max_value = maxv
        if minv < min_value:
            min_value = minv
    return min_value, max_value


def read_nii(filepath):
    """ Reads and returns nparray data from single .nii image"""
    img = nib.load(filepath)
    img_data = img.get_fdata()
    return img_data


def normalise(image):   #todo test
    """ If minv = 0, then is equiv to dividing all values by image maximum value
    :param image: data image
    :param minv: minimum voxel value
    :param maxv: maximum voxel value
    :return: normalised image
    """
    maxv = np.amax(image)
    minv = np.amin(image)
    img_norm = (image - minv) / (maxv - minv)
    img_norm = img_norm.astype("float64")
    return img_norm


def normalise2(path):  #todo test, not complete, needs to iterate thru path
    """ """
    image = read_nii(path)
    maxv = np.amax(image)
    minv = np.amin(image)
    img_norm = (image - minv) / (maxv - minv)
    img_norm = img_norm.astype("float64")
    return img_norm


def z_norm(image):    #todo test
    """ Returns z normalised image. This will involve negative values. May require adjusted
    colour palette to avoid all neg values being coloured black.
    :param image:
    :return: z normalised image
    """
    return (image - np.mean(image)) / np.std(image)