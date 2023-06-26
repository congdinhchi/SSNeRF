# Render color

import torch
import torch.nn as nn

import models
from models.utils import get_activation
from models.network_utils import get_encoding, get_mlp
from systems.utils import update_module_step


@models.register('volume-brightness')
class VolumeBrightness(nn.Module):
    def __init__(self, config):
        super(VolumeBrightness, self).__init__()
        self.config = config
        self.n_ori_dims = self.config.get('n_dir_dims', 3)
        self.n_output_dims = 1

        encoding = get_encoding(self.n_ori_dims, self.config.dir_encoding_config)

        self.n_input_dims = encoding.n_output_dims + self.config.input_feature_dim #16 +16
        network = get_mlp(self.n_input_dims, self.n_output_dims, self.config.mlp_network_config)    
        self.encoding = encoding
        self.network = network
    
    def forward(self, features, origins, *args):
        """
        Args:
            origins torch.Size([97790, 3])
            features: torch.Size([97790, 16])

        Result:
            brightness: torch.Size([97790, 1])
        """
        origins = (origins + 1.) / 2. # (-1, 1) => (0, 1)
        origins_embd = self.encoding(origins.view(-1, self.n_ori_dims)) # origins_embd torch.Size([97790, 16])
        print(f"features {len([features.view(-1, features.shape[-1]), origins_embd])}")
        network_inp = torch.cat([features.view(-1, features.shape[-1]), origins_embd] + [arg.view(-1, arg.shape[-1]) for arg in args], dim=-1) #([97790, 32])
        #*features.shape[:-1] => [97790,]
        brightness = self.network(network_inp).view(*features.shape[:-1], self.n_output_dims).float()

        # Dung cho neus
        if 'brightness_activation' in self.config:
            print("chay den brightness_activation")
            brightness = get_activation(self.config.brightness_activation)(brightness)
        return brightness

    def update_step(self, epoch, global_step):
        update_module_step(self.encoding, epoch, global_step)

    def regularizations(self, out):
        return {}


@models.register('volume-color')
class VolumeColor(nn.Module):
    def __init__(self, config):
        super(VolumeColor, self).__init__()
        self.config = config
        self.n_output_dims = 3
        self.n_input_dims = self.config.input_feature_dim
        network = get_mlp(self.n_input_dims, self.n_output_dims, self.config.mlp_network_config)
        self.network = network
    
    def forward(self, features, *args):
        network_inp = features.view(-1, features.shape[-1])
        color = self.network(network_inp).view(*features.shape[:-1], self.n_output_dims).float()
        if 'color_activation' in self.config:
            color = get_activation(self.config.color_activation)(color)
        return color

    def regularizations(self, out):
        return {}