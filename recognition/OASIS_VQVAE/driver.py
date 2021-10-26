import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory
from vqvae import VQVAE, get_closest_embedding_indices

import numpy as np
import matplotlib.pyplot as plt

import argparse

class SSIMCallback(tf.keras.callbacks.Callback):
    def __init__(self, validation_data, shift=0.0):
        super(SSIMCallback, self).__init__()
        self._val = validation_data
        self._shift = shift

    def on_epoch_end(self, epoch, logs):
        total_count = 0.0
        total_ssim = 0.0

        for batch in self._val:
            recon = self.model.predict(batch)
            total_ssim += tf.math.reduce_sum(tf.image.ssim(batch + self._shift, recon + self._shift, max_val=1.0))
            total_count += batch.shape[0]

        logs['val_avg_ssim'] = (total_ssim/total_count).numpy()
        print("epoch: {:d} - val_avg_ssim: {:.6f}".format(epoch, logs['val_avg_ssim']))


def plot_history(history):
    plt.plot(history.history['loss'])
    plt.title('total training loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.show()

    plt.plot(history.history['reconstruction_loss'])
    plt.title('training reconstruction loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.show()

    plt.plot(history.history['vq_loss'])
    plt.title('training quantizer loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.show()

    plt.plot(history.history['val_avg_ssim'])
    plt.title('validation dataset average SSIM')
    plt.ylabel('average SSIM')
    plt.xlabel('epoch')
    plt.show()


def show_image_and_reconstruction(original, cb, reconstructed):
    plt.subplot(1, 3, 1)
    plt.imshow(original, cmap="gray")
    plt.title("Original")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(cb)
    plt.title("Codebook")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.imshow(reconstructed, cmap="gray")
    plt.title("Reconstructed")
    plt.axis("off")

    plt.show()


def load_images(location, image_size, batch_size):
    return image_dataset_from_directory(location, 
                                        label_mode=None, 
                                        image_size=image_size,
                                        color_mode="grayscale",
                                        batch_size=batch_size,
                                        shuffle=True)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="VQVAE trainer")

    parser.add_argument("--data", required=True, type=str, help="Location of unzipped OASIS dataset. Folder should contain the folders 'keras_png_slices_train' and 'keras_png_slices_validate'.")

    parser.add_argument("--K", "--num-embeddings", type=int, default=512, help="Number of embeddings, described as K in the VQVAE paper (default: 512)")
    parser.add_argument("--D", "--embedding-dim", type=int, default=2, help="Size of the embedding vectors, described as D in the VQVAE paper (default: 2)")
    parser.add_argument("--beta", type=float, default=1.5, help="Committment cost, described as beta in VQVAE paper (default: 1.5)")

    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs to train for (default: 30)")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training (default: 32)")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate for ADAM optimiser (default 2e-4)")

    parser.add_argument("--shift", type=float, default=0.5, help="Normalisation shift that will be subtracted from each pixel value prior to training (default: 0.5)")

    args = parser.parse_args()

    # load OASIS images from folder
    IMG_SIZE = 256

    dataset             = load_images(args.data + "/keras_png_slices_train", (IMG_SIZE, IMG_SIZE), args.batch_size)
    dataset_validation  = load_images(args.data + "/keras_png_slices_validate", (IMG_SIZE, IMG_SIZE), args.batch_size)

    # normalize pixels (in [0,255]) between [-SHIFT, -SHIFT + 1] (for example: [-0.5, 0.5])
    dataset             = dataset.map(lambda x: (x / 255.0) - args.shift)
    dataset_validation  = dataset_validation.map(lambda x: (x / 255.0) - args.shift)

    # calculate variance of training data (at a individual pixel level) to pass into VQVAE
    count = dataset.unbatch().reduce(tf.cast(0, tf.int64), lambda x,_: x + 1 ).numpy()
    mean = dataset.unbatch().reduce(tf.cast(0, tf.float32), lambda x,y: x + y ).numpy().flatten().sum() / (count * IMG_SIZE * IMG_SIZE)
    var = dataset.unbatch().reduce(tf.cast(0, tf.float32), lambda x,y: x + tf.math.pow(y - mean,2)).numpy().flatten().sum() / (count * IMG_SIZE * IMG_SIZE - 1)

    # create model
    input_size = (IMG_SIZE, IMG_SIZE, 1)
    vqvae_model = VQVAE(input_size, args.D, args.K, args.beta, var)

    vqvae_model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate))

    # fit it
    history = vqvae_model.fit(dataset, 
                              epochs=args.epochs, 
                              batch_size=args.batch_size, 
                              callbacks=[SSIMCallback(dataset_validation, args.shift)])

    # plot history
    plot_history(history)

    # visualise some reconstructions
    num_batches_to_show = 2
    num_images_per_batch_to_show = 5

    test_images_batches = dataset.take(num_batches_to_show)
    for test_images in test_images_batches.as_numpy_iterator():
        reconstructions = vqvae_model.predict(test_images)

        encoder_outputs = vqvae_model.encoder().predict(test_images)
        encoder_outputs_flat = encoder_outputs.reshape(-1, encoder_outputs.shape[-1])

        codebook_indices = get_closest_embedding_indices(vqvae_model.quantizer().embeddings(), encoder_outputs_flat)
        codebook_indices = codebook_indices.numpy().reshape(encoder_outputs.shape[:-1])

        for i in range(num_images_per_batch_to_show):
            # add the shfit back to the images to undo the initial shifting (e.g. go from [-0.5, 0.5] to [0,1])
            original_image = tf.reshape(test_images[i], (1, IMG_SIZE, IMG_SIZE, 1)) + args.shift
            reconstructed_image = tf.reshape(reconstructions[i], (1, IMG_SIZE, IMG_SIZE, 1)) + args.shift
            codebook_image = codebook_indices[i]

            show_image_and_reconstruction(tf.squeeze(original_image), codebook_image, tf.squeeze(reconstructed_image))
            ssim = tf.math.reduce_sum(tf.image.ssim(original_image, reconstructed_image, max_val=1.0)).numpy()
            print("SSIM: ", ssim)
