import fnmatch
import os
import nibabel as nib
import numpy as np
import pandas as pd
import datetime

from model import UNetCSIROMalePelvic


def read_and_split_data(processed_data_dir, split_perc_arr, split_names_arr, verbose=False):
    x_files = np.array(fnmatch.filter(sorted(os.listdir(processed_data_dir)), '*.nii.gz'))
    x_files = x_files[np.array([not fnmatch.fnmatch(filename, '*SEMANTIC*') for filename in x_files])]
    y_files = np.array(fnmatch.filter(sorted(os.listdir(processed_data_dir)), '*SEMANTIC*.nii.gz'))
    print('#X:{}, #Y:{}'.format(len(x_files), len(y_files))) if verbose else None

    x_files = pd.DataFrame(x_files)
    x_files.columns = ['x_filename']
    x_files = pd.merge(x_files, x_files['x_filename'].str.split('_', 10, expand=True),
                       left_index=True, right_index=True)
    x_files.columns = ['x_filename', 'preamble', 'case_num', 'observation_num', 'aug', 'aug_num', 'aug_type', 'suffix']
    x_files = x_files[['preamble', 'case_num', 'observation_num', 'aug_num', 'aug_type', 'x_filename']]
    x_files['x_filepath'] = x_files['x_filename'].apply(lambda x: processed_data_dir + '/' + x)

    y_files = pd.DataFrame(y_files)
    y_files.columns = ['y_filename']
    y_files = pd.merge(y_files, y_files['y_filename'].str.split('_', 10, expand=True),
                       left_index=True, right_index=True)
    y_files.columns = ['y_filename', 'preamble', 'case_num', 'observation_num', 'aug', 'aug_num', 'aug_type',
                       'semantic', 'suffix']
    y_files = y_files[['preamble', 'case_num', 'observation_num', 'aug_num', 'aug_type', 'y_filename']]
    y_files['y_filepath'] = y_files['y_filename'].apply(lambda y: processed_data_dir + '/' + y)

    data_files = pd.merge(x_files, y_files, how='inner',
                          left_on=['preamble', 'case_num', 'observation_num', 'aug_num', 'aug_type'],
                          right_on=['preamble', 'case_num', 'observation_num', 'aug_num', 'aug_type'])

    # Distinct cases out of all successfully
    # merged X,Y pairs of images
    unique_cases = data_files['case_num'].unique()
    unique_cases = pd.DataFrame(unique_cases, columns=['case_num'])
    num_unique_cases = len(unique_cases)

    split_counts = np.round(split_perc_arr * num_unique_cases, decimals=0)
    split_counts = np.array(split_counts, dtype=np.int32)

    actual_splits = np.empty(num_unique_cases, dtype='<U11')
    i = 0
    for idx, curr_split_count in enumerate(split_counts):
        actual_splits[i: i + curr_split_count] = str(split_names_arr[idx])
        i += curr_split_count
        pass

    # Randomize
    np.random.shuffle(actual_splits)
    # Enforce correct length in case of round-up errors
    actual_splits = actual_splits[0:num_unique_cases]
    actual_splits = pd.DataFrame(actual_splits, columns=['split_type'])
    # Join with unique cases
    unique_cases = pd.merge(unique_cases, actual_splits, how='inner', left_index=True, right_index=True)

    # Join back with main dataframe
    data_files = pd.merge(data_files, unique_cases, how='inner', left_on='case_num', right_on='case_num')

    return data_files


def main():

    cleaned_data_dir = ''

    print(np.__version__)
    # need 1.18.5

    # Create the model
    the_model = UNetCSIROMalePelvic("My Model")

    print(the_model.mdl.summary())

    for layer in the_model.mdl.layers:
        print(layer.input_shape, '-->', layer.name, '-->', layer.output_shape)
        pass

    # Create Train / Val / Test splits
    split_perc_arr = np.array([0.4, 0.4, 0.2], dtype=np.float32)
    split_names_arr = np.array(['train', 'val', 'test'])
    master_df = read_and_split_data(cleaned_data_dir, split_perc_arr, split_names_arr)

    print(master_df.info(verbose=True))

    # Collect a training sample
    sample = master_df[master_df['split_type'] == 'train'].sample(n=1)

    # Load it into memory
    curr_x = nib.load(sample.x_filepath.item()).get_fdata()
    curr_y = nib.load(sample.y_filepath.item()).get_fdata()

    print("Start Training at {}".format(datetime.datetime.now()))
    # Add a dimension at the start for Batch Size of 1
    curr_x = curr_x[None, ...]
    curr_y = curr_y[None, ...]

    print(curr_x.shape)
    print(curr_y.shape)

    #print(curr_y)

    result = the_model.mdl.train_on_batch(x=curr_x, y=curr_y)
    the_model.train_batch_count += 1
    print("Finish Training at {}".format(datetime.datetime.now()))

    print('result of training:')
    print(result)

    pass


# Run the program
main()