import os
import os.path as osp

import torch

from .dataset import Dataset
from .utils.download import download_url
from .utils.extract import extract_zip
from .utils.spinner import Spinner
from .utils.tu_format import tu_files, read_tu_set


class Cuneiform(Dataset):
    url = 'https://ls11-www.cs.uni-dortmund.de/people/morris/' \
          'graphkerneldatasets/Cuneiform.zip'
    prefix = osp.join('Cuneiform', 'Cuneiform')

    def __init__(self, root, split=None, transform=None):
        super(Cuneiform, self).__init__(root, transform)
        self.set = torch.load(self._processed_files[0])

        if split is None:
            g = self.set.num_graphs
            self.split = torch.arange(0, g, out=torch.LongTensor())
        else:
            self.split = split

    def __getitem__(self, i):
        return super(Cuneiform, self).__getitem__(self.split[i])

    def __len__(self):
        return self.split.size(0)

    @property
    def raw_files(self):
        return tu_files(
            self.prefix,
            graph_indicator=True,
            graph_labels=True,
            node_attributes=True,
            node_labels=True)

    @property
    def processed_files(self):
        return 'data.pt'

    def download(self):
        file_path = download_url(self.url, self.raw_folder)
        extract_zip(file_path, self.raw_folder)
        os.unlink(file_path)

    def process(self):
        spinner = Spinner('Processing').start()

        set = read_tu_set(
            self.raw_folder,
            self.prefix,
            graph_indicator=True,
            graph_labels=True,
            node_attributes=True,
            node_labels=True)

        set.pos = set.input[:, :2]
        set.input = set.input[:, 2:]

        spinner.success()

        return set
