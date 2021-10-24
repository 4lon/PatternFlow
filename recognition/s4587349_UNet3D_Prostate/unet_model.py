
# import keras.layers
# from keras.layers import *
# from keras.models import *
# from keras.optimizers import *
import tensorflow as tf
import tensorflow.keras
import support_methods as sm
import driver as drv
# from support_methods import *


def unet3d(inputsize= (256,256,128,1), kernelSize=3):
    inputs = tf.keras.layers.Input(inputsize)

    # todo dropout d4 = Dropout(0.5)(c4)
    c1 = tf.keras.layers.Conv3D(32, kernelSize, padding='same', kernel_initializer='he_normal')(inputs)   #with relu removed
    # c1 = Conv3D(32, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(inputs)
    c1 = tf.keras.layers.BatchNormalization()(c1)
    # c1 = ReLU(c1)
    # c1 = keras.layers.ReLU(c1)
    c1 = tf.keras.activations.relu(c1)  #todo if this helps. Bo - not clear if BN before Relu helps, or if reverse is better
    c1 = tf.keras.layers.Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c1)
    c1 = tf.keras.layers.BatchNormalization()(c1)
    p1 = tf.keras.layers.MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c1)  #todo padding="same"?

    c2 = tf.keras.layers.Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p1)
    c2 = tf.keras.layers.BatchNormalization()(c2)
    c2 = tf.keras.layers.Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c2)
    c2 = tf.keras.layers.BatchNormalization()(c2)
    p2 = tf.keras.layers.MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c2)

    c3 = tf.keras.layers.Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p2)
    c3 = tf.keras.layers.BatchNormalization()(c3)
    c3 = tf.keras.layers.Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c3)
    c3 = tf.keras.layers.BatchNormalization()(c3)
    p3 = tf.keras.layers.MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c3)

    c4 = tf.keras.layers.Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p3)
    c4 = tf.keras.layers.BatchNormalization()(c4)
    c4 = tf.keras.layers.Conv3D(512, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c4)
    c4 = tf.keras.layers.BatchNormalization()(c4)

    # todo is this right for transpose layer
    # u5 = Conv3D(512, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c4))
    u5 = tf.keras.layers.Conv3DTranspose(512, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c4)
    concat5 = tf.keras.layers.Concatenate(axis=4)([c3,u5])
    c5 = tf.keras.layers.Conv3D(768, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat5)
    c5 = tf.keras.layers.BatchNormalization()(c5)
    c5 = tf.keras.layers.Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c5)
    c5 = tf.keras.layers.BatchNormalization()(c5)

    # u6 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c5))
    u6 = tf.keras.layers.Conv3DTranspose(256, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c5)
    concat6 = tf.keras.layers.Concatenate(axis=4)([c2,u6])
    # need Upsampling3D(size=2)(c5)  rather than conv3DTranspose
    # or both?
    c6 = tf.keras.layers.Conv3D(768, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat6)
    c6 = tf.keras.layers.BatchNormalization()(c6)
    c6 = tf.keras.layers.Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c6)
    c6 = tf.keras.layers.BatchNormalization()(c6)

    # u7 = Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c6))
    u7 = tf.keras.layers.Conv3DTranspose(128, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c6)
    concat7 = tf.keras.layers.Concatenate(axis=4)([c1,u7])
    c7 = tf.keras.layers.Conv3D(192, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat7)
    c7 = tf.keras.layers.BatchNormalization()(c7)
    c7 = tf.keras.layers.Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c7)
    c7 = tf.keras.layers.BatchNormalization()(c7)
    c7 = tf.keras.layers.Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c7)
    c7 = tf.keras.layers.BatchNormalization()(c7)

    outputs = tf.keras.layers.Conv3D(drv.CLASSES, (1,1,1), activation="softmax")(c7)

    model = tf.keras.layers.Model(inputs=[inputs], outputs = [outputs])
    return model
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'] ) # todo add dsc
    model.summary()


# def unet3d_backup(inputsize= (256,256,128,1), kernelSize=3):
#     inputs = tf.keras.layers.Input(inputsize)
#
#     # todo dropout d4 = Dropout(0.5)(c4)
#     c1 = tf.keras.layers.Conv3D(32, kernelSize, padding='same', kernel_initializer='he_normal')(inputs)   #with relu removed
#     # c1 = Conv3D(32, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(inputs)
#     c1 = BatchNormalization()(c1)
#     # c1 = ReLU(c1)
#     # c1 = keras.layers.ReLU(c1)
#     c1 = tf.keras.activations.relu(c1)  #todo if this helps. Bo - not clear if BN before Relu helps, or if reverse is better
#     c1 = Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c1)
#     c1 = BatchNormalization()(c1)
#     p1 = MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c1)  #todo padding="same"?
#
#     c2 = Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p1)
#     c2 = BatchNormalization()(c2)
#     c2 = Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c2)
#     c2 = BatchNormalization()(c2)
#     p2 = MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c2)
#
#     c3 = Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p2)
#     c3 = BatchNormalization()(c3)
#     c3 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c3)
#     c3 = BatchNormalization()(c3)
#     p3 = MaxPooling3D(pool_size=(2, 2, 2), strides=(2, 2, 2))(c3)
#
#     c4 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(p3)
#     c4 = BatchNormalization()(c4)
#     c4 = Conv3D(512, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c4)
#     c4 = BatchNormalization()(c4)
#
#     # todo is this right for transpose layer
#     # u5 = Conv3D(512, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c4))
#     u5 = Conv3DTranspose(512, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c4)
#     concat5 = Concatenate(axis=4)([c3,u5])
#     c5 = Conv3D(768, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat5)
#     c5 = BatchNormalization()(c5)
#     c5 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c5)
#     c5 = BatchNormalization()(c5)
#
#     # u6 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c5))
#     u6 = Conv3DTranspose(256, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c5)
#     concat6 = Concatenate(axis=4)([c2,u6])
#     # need Upsampling3D(size=2)(c5)  rather than conv3DTranspose
#     # or both?
#     c6 = Conv3D(768, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat6)
#     c6 = BatchNormalization()(c6)
#     c6 = Conv3D(256, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c6)
#     c6 = BatchNormalization()(c6)
#
#     # u7 = Conv3D(128, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(UpSampling3D(size=(2,2,2))(c6))
#     u7 = Conv3DTranspose(128, kernelSize, strides=(2, 2, 2), activation='relu', padding='same', kernel_initializer='he_normal')(c6)
#     concat7 = Concatenate(axis=4)([c1,u7])
#     c7 = Conv3D(192, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(concat7)
#     c7 = BatchNormalization()(c7)
#     c7 = Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c7)
#     c7 = BatchNormalization()(c7)
#     c7 = Conv3D(64, kernelSize, activation='relu', padding='same', kernel_initializer='he_normal')(c7)
#     c7 = BatchNormalization()(c7)
#
#     outputs = Conv3D(drv.CLASSES, (1,1,1), activation="softmax")(c7)
#
#     model = Model(inputs=[inputs], outputs = [outputs])
#     return model
#     model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'] ) # todo add dsc
#     model.summary()






