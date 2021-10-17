import tensorflow as tf
import pathlib
import os
import matplotlib.pyplot as plt

class DataLoader:

    def __init__(self, path, batch_size=32, validation_size=0.2, test_size=0.1):
        # ISIC2018_Task1-2_Training_Data\\

        self.path = path
        self.batch_size = batch_size
        self.image_shape = [384, 512]

        list_ds = tf.data.Dataset.list_files(self.path + "ISIC2018_Task1-2_Training_Input_x2\\*.jpg", shuffle=False)

        data_dir = pathlib.Path(self.path)
        image_count = len(list(self.data_dir.glob('ISIC2018_Task1-2_Training_Input_x2\\*.jpg')))

        # Validation size: 0.2, Test size: 0.1
        val_size = int(image_count * validation_size)
        test_size = int(image_count * test_size)
        train_ds = list_ds.skip(val_size)
        val_ds = list_ds.take(val_size)
        test_ds = train_ds.take(test_size)
        train_ds = train_ds.skip(test_size)

        @tf.function
        def get_mask(file_path):
            parts = tf.strings.split(file_path, os.path.sep)
            file_name = tf.strings.split(parts[-1], '.')[0]
            file_name = file_name + '_segmentation.png'
            return 'ISIC2018_Task1-2_Training_Data\\ISIC2018_Task1_Training_GroundTruth_x2\\' + file_name

        @tf.function
        def process_path(file_path):
            # Output raw image data from file paths
            img = tf.io.decode_jpeg(tf.io.read_file(file_path), channels=3)
            mask = tf.io.decode_png(tf.io.read_file(get_mask(file_path)), channels=1)
            img = tf.image.resize(img, self.image_shape)
            mask = tf.image.resize(mask, self.image_shape)
            img = tf.cast(img, tf.float32) / 255.0
            mask = tf.cast(mask, tf.float32) / 255.0

            img = tf.reshape(img, tuple(self.image_shape + [3]))
            img = tf.reshape(mask, tuple(self.image_shape + [1]))
            return img, mask

        @tf.function
        def configure_for_performance(ds):
            ds = ds.cache()
            ds = ds.shuffle(buffer_size=200)
            ds = ds.batch(32)
            ds = ds.prefetch(self.AUTOTUNE)

            return ds

        # Process Dataset
        self.AUTOTUNE = tf.data.AUTOTUNE

        train_ds = train_ds.map(process_path, num_parallel_calls=self.AUTOTUNE)
        val_ds = val_ds.map(process_path, num_parallel_calls=self.AUTOTUNE)
        test_ds = test_ds.map(process_path, num_parallel_calls=self.AUTOTUNE)

        self.train_ds = configure_for_performance(train_ds)
        self.val_ds = configure_for_performance(val_ds)
        self.test_ds = configure_for_performance(test_ds)

    def get_data_size(self):
        print("Training set: " + tf.data.experimental.cardinality(self.train_ds).numpy())
        print("Validation set: " + tf.data.experimental.cardinality(self.val_ds).numpy())
        print("Test set: " + tf.data.experimental.cardinality(self.test_ds).numpy())

    def show_images(self):
        image_batch, label_batch = next(iter(self.train_ds))

        plt.figure(figsize=(10, 10))
        for i in [1,3,5]:
            ax = plt.subplot(3, 2, i)
            plt.imshow(image_batch[i].numpy().astype("uint8"))
            plt.axis("off")
            ax = plt.subplot(3, 2, i + 1)
            plt.imshow(label_batch[i].numpy().astype("uint8"))
            plt.axis("off")

    def get_training_set(self):
        return self.train_ds

    def get_validation_set(self):
        return self.val_ds

    def get_test_set(self):
        return self.test_ds