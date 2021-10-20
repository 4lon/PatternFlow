import torch
import torch.nn as nn

class VQVAE(nn.Module):
    def __init__(self, img_channels, latent_size, latent_dim):
        super(VQVAE, self).__init__()
        
        self.K = latent_size
        self.D = latent_dim
        
        self.encoder = nn.Sequential(
            nn.Conv2d(img_channels, 16, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=4, stride=2, padding=1),
            nn.ReLU()
        )
        
        self.codebook = nn.Embedding(self.K, self.D)
        self.codebook.weight.data.uniform_(-1/self.K, 1/self.K)
        
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(32, 16, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(16, img_channels, kernel_size=4, stride=2, padding=1),
            nn.ReLU() 
        )
        
    def vector_quantize(self, z_e):
        z_e = z_e.permute(0, 2, 3, 1).contiguous()
        
        distances = torch.abs(
            torch.sum(z_e.view(-1, self.D).pow(2), dim=1, keepdim=True) - 
            torch.sum(self.codebook.weight.pow(2), dim=1))
        
        embedding_indices = torch.argmin(distances, dim=1, keepdim=True)
        q_ont_hot = torch.zeros(distances.shape)
        q_ont_hot.scatter_(1, embedding_indices, 1)
        
        z_q = torch.matmul(q_ont_hot, self.codebook.weight).view(z_e.shape)
        z_q = z_e + (z_q - z_e).detach()
        
        return z_q.permute(0, 3, 1, 2).contiguous()
    
    def forward(self, imgs):
        z_e = self.encoder(imgs)
        encoded = self.vector_quantize(z_e)
        decoded = self.decoder(encoded)
        
        return z_e, encoded, decoded
    
    