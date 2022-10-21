#Imports
from dataset.py import ISIC_Dataset
from modules.py import UNet, dice_loss
import torch
from torch.utils.data import DataLoader

#Variables
BATCH_SIZE = 1
EPOCHS = 1

#Import GPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#Load Training and Validation Data
train_image_path = "./ISIC-2017_Training_Data"
train_segmentation_path = "./ISIC-2017_Training_Part1_GroundTruth"
valid_image_path = "./ISIC-2017_Validation_Data"
valid_segmentation_path = "./ISIC-2017_Validation_Part1_GroundTruth"

train_dataset = ISIC_Dataset(train_image_path, train_segmentation_path)
valid_dataset = ISIC_Dataset(valid_image_path, valid_segmentation_path)

trainloader = DataLoader(dataset=train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)

#Create model to train
model = UNet().to(device)
save_path = "./Trained_Model.pth"

#Optimiser as per paper
optimizer = torch.optim.Adam(model.parameters(), lr=0.0005, weight_decay=0.0001)

#Training Loop that records metrics
for epoch in range(epochs):

    #Training
    model.train()

    for i, (imgs, truths) in enumerate(trainloader):
      imgs = imgs.to(device)
      truths = truths.to(device)

      #Zero the gradient
      optimizer.zero_grad()

      #Forward Pass
      outputs = model(imgs)

      #Calculate loss
      loss = dice_loss(outputs, truths)
      print("DICE Loss ", loss)
      loss.backward()
      optimizer.step()

      #Validation would go here

    #Save Trained weights
    torch.save(model.state_dict(), save_path)
