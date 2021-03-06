import torch
from torch.autograd import Function

from ...sparse import SparseTensor


class SparseMM(Function):
    def __init__(self, sparse):
        super(SparseMM, self).__init__()
        self.sparse = sparse

    def forward(self, dense):
        return torch.mm(self.sparse, dense)

    def backward(self, grad_output):
        grad_input = None
        if self.needs_input_grad[0]:
            grad_input = torch.mm(self.sparse.t(), grad_output)
        return grad_input


def add_self_loops(edge_index, n):
    loop = torch.arange(0, n, out=edge_index.new()).unsqueeze(0).repeat(2, 1)
    return torch.cat([edge_index, loop], dim=1)


def graph_conv(x, edge_index, edge_attr, weight, bias=None):
    row, col = edge_index
    n, e = x.size(0), row.size(0)

    if edge_attr is None:
        edge_attr = x.data.new(e).fill_(1)

    # Compute degree.
    degree = x.data.new(n).fill_(0).scatter_add_(0, row, edge_attr) + 1
    degree = degree.pow_(-0.5)

    # Normalize and append adjacency matrix by self loops.
    edge_attr = edge_attr * degree[row]
    edge_attr *= degree[col]
    edge_attr = torch.cat([edge_attr, degree * degree], dim=0)
    edge_index = add_self_loops(edge_index, n)
    adj = SparseTensor(edge_index, edge_attr, torch.Size([n, n]))

    # Convolution.
    output = SparseMM(adj)(torch.mm(x, weight))

    if bias is not None:
        output += bias

    return output
