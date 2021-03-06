import os.path as osp

import torch
from numpy import bincount
from torch import LongTensor as Long
from torch_geometric.read import read_txt
from torch_geometric.utils import coalesce, one_hot
from torch_geometric.data import Data


def filename(prefix, name, path=None):
    name = '{}_{}.txt'.format(prefix, name)
    return name if path is None else osp.join(path, name)


def cat(*seq):
    seq = [t for t in seq if t is not None]
    seq = [t.unsqueeze(-1) if t.dim() == 1 else t for t in seq]
    return torch.cat(seq, dim=-1).squeeze() if len(seq) > 0 else None


def get_tu_filenames(prefix,
                     graph_indicator=False,
                     graph_attributes=False,
                     graph_labels=False,
                     node_attributes=False,
                     node_labels=False,
                     edge_attributes=False,
                     edge_labels=False):

    names = ['A'] + [key for key, value in locals().items() if value is True]
    return [filename(prefix, name) for name in names]


def read_tu_files(path,
                  prefix,
                  graph_indicator=False,
                  graph_attributes=False,
                  graph_labels=False,
                  node_attributes=False,
                  node_labels=False,
                  edge_attributes=False,
                  edge_labels=False):

    file_path = filename(prefix, 'A', path)
    edge_index = read_txt(file_path, sep=',', out=Long()) - 1
    edge_index, perm = coalesce(edge_index.t())

    x = tmp1 = tmp2 = None
    if node_attributes:
        file_path = filename(prefix, 'node_attributes', path)
        tmp1 = read_txt(file_path, sep=',')
    if node_labels:
        file_path = filename(prefix, 'node_labels', path)
        tmp2 = one_hot(read_txt(file_path, sep=',', out=Long()) - 1)
    x = cat(tmp1, tmp2)

    edge_attr = tmp1 = tmp2 = None
    if edge_attributes:
        file_path = filename(prefix, 'edge_attributes', path)
        tmp1 = read_txt(file_path, sep=',')[perm]
    if edge_labels:
        file_path = filename(prefix, 'edge_labels', path)
        tmp2 = read_txt(file_path, sep=',')[perm] - 1
    edge_attr = cat(tmp1, tmp2)

    y = None
    if graph_attributes:  # Regression problem.
        file_path = filename(prefix, 'graph_attributes', path)
        y = read_txt(file_path, sep=',')
    if graph_labels:  # Classification problem.
        file_path = filename(prefix, 'graph_labels', path)
        y = read_txt(file_path, sep=',', out=Long()) - 1

    dataset = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)

    if graph_indicator:
        file_path = filename(prefix, 'graph_indicator', path)
        graph_indicator = read_txt(file_path, out=Long()) - 1
    else:
        graph_indicator = Long(x.size(0)).fill_(0)

    return compute_slices(dataset, graph_indicator)


def compute_slices(dataset, graph_indicator):
    num_nodes = graph_indicator.size(0)
    graph_slice = torch.arange(0, graph_indicator[-1] + 2, out=Long())

    node_slice = torch.cumsum(Long(bincount(graph_indicator)), dim=0)
    node_slice = torch.cat([Long([0]), node_slice], dim=0)

    row, _ = dataset.edge_index
    graph_indicator = graph_indicator[row]
    edge_slice = torch.cumsum(Long(bincount(graph_indicator)), dim=0)
    edge_slice = torch.cat([Long([0]), edge_slice], dim=0)

    # Edge indices should start at zero for every graph.
    dataset.edge_index -= node_slice[graph_indicator].unsqueeze(0)

    slices = {'edge_index': edge_slice}
    if dataset.x is not None:
        slices['x'] = node_slice
    if dataset.edge_attr is not None:
        slices['edge_attr'] = edge_slice
    if dataset.y is not None:
        y_slice = node_slice if dataset.y.size(0) == num_nodes else graph_slice
        slices['y'] = y_slice

    return dataset, slices
