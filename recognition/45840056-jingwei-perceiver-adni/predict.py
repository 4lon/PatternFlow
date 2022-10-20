import numpy as np
import torch
from torch.utils.data import random_split, DataLoader
from dataset import ADNI, dataset_dir
from train import print_accuracy

def predict(model, ds, batch_size=8):
    loader = DataLoader(ds, shuffle=True, batch_size=batch_size)
    batch, labels = next(iter(loader))
    print(f"true labels:\n{labels}")
    pred = model(batch)
    print(f"predictions:\n{torch.round(pred)}")

if __name__ == "__main__":
    batch_size = 8
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.load("model.pkl").to(device)
    ds = ADNI(device, dataset_dir)
    other_size  = int(np.round(ADNI.NUM_SEQUENCES * 0.8))
    ts_size  = int(np.round(ADNI.NUM_SEQUENCES * 0.2))
    ds, ts_ds = random_split(ds, (other_size, ts_size), torch.Generator().manual_seed(42))
    print_accuracy(model, ts_ds, batch_size)
