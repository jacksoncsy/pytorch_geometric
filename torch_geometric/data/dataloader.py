import torch.utils.data
from torch_geometric.data import Data, collate_to_batch


def collate(batch):
    if type(batch[0]) is Data:
        return collate_to_batch(batch)

    return torch.utils.data.dataloader.default_collate(batch)


class DataLoader(torch.utils.data.DataLoader):
    def __init__(self, dataset, **kwargs):
        super(DataLoader, self).__init__(dataset, collate_fn=collate, **kwargs)
