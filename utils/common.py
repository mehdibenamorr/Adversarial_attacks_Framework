import torch
from torchvision import datasets, transforms
import os
import pickle
import matplotlib.pyplot as plt
import numpy as np
from igraph import *
from utils.differential_evolution import differential_evolution

def flat_trans(x):
    x.resize_(28*28)

    return x

def generate_samples(model):

    mnist_transform = transforms.Compose([ transforms.ToTensor(),transforms.Normalize((0.1307,), (0.3081,)),transforms.Lambda(flat_trans)]) if model != "CNN" else \
        transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('data/'+model, train=False, transform=mnist_transform),
        batch_size=1, shuffle=True, num_workers= 2)
    # images, labels = [], []
    # for idx, data in enumerate(test_loader):
    #     x_lots, y_lots = data
    #     for x, y in zip(x_lots, y_lots):
    #         images.append(x.numpy())
    #         labels.append(y)
    #
    # data_dict = {"images": images, "labels": labels}
    # with open("data/"+model+"/10k_samples.pkl", "wb") as f:
    #     pickle.dump(data_dict, f)
    return test_loader


def vis_adv_org(x_org, x_adv,y_pred,y_adv,target=None):
    noise = (x_adv - x_org).data.numpy().reshape(28,28)
    x_org = x_org.data.numpy().reshape(28,28)
    x_adv = x_adv.data.numpy().reshape(28,28)
    disp_im = np.concatenate((x_org, x_adv,noise),axis=1)
    if target:
        plt.title("Original : {}    Target/Adv : {}/{}    Perturbation : {:.5f}".format(y_pred,target,y_adv,noise.mean()))
    else:
        plt.title("Original : {}    Adversarial : {}    Perturbation : {:.5f}".format(y_pred,y_adv,noise.mean()))
    plt.imshow(disp_im,cmap='gray')
    plt.show()



def generate_random_dag(N, k, p, dense=-1):
    if dense == 1:
        g = Graph()
        for x in range(N):
            g.add_vertex(x)
        adj_matrix = np.tril(np.array(g.get_adjacency().data))
        g = Graph.Adjacency((adj_matrix>0).tolist())
        g.to_directed()
    elif dense == 2:
        g = Graph()
        for x in range(N):
            g.add_vertex(x)
        for i in range(int(N/2)):
            for j in range(int(N/2)):
                g.add_edge(i,int(N/2)+j)
        adj_matrix = np.tril(np.array(g.get_adjacency().data))
        g = Graph.Adjacency((adj_matrix>0).tolist())
        g.to_directed()
    else:
        g = Graph.Watts_Strogatz(1,N,k,p)
        adj_matrix = np.tril(np.array(g.get_adjacency().data))
        g = Graph.Adjacency((adj_matrix>0).tolist())
        g.to_directed()
    return g


def layer_indexing(g):
    # vertices_index = [-1 for i in range(len(g.vs))]
    # for v in g.vs:
    #     if v.indegree() == 0:
    #         vertices_index[v.index] = 0
    # num_unindexed_vertices = len(g.vs)
    unindexed_vertices = [v for v in g.vs if v.indegree() > 0]
    vertices_index = [0 if v.indegree() < 1 else -1 for v in g.vs]
    while len(unindexed_vertices) > 0 :
        for v in unindexed_vertices:
            in_edges = v.predecessors()
            ind = { vertices_index[vv.index] for vv in in_edges }
            if -1 not in ind:
                vertices_index[v.index] = max(ind) + 1
                unindexed_vertices.remove(v)
            else:
                continue
    vertex_by_layers = [ [] for k in range(max(vertices_index)+1)]
    for i in range(len(vertices_index)):
        if g.vs[i].outdegree() < 1:
            vertex_by_layers[-1].append(g.vs[i])
        else:
            vertex_by_layers[vertices_index[i]].append(g.vs[i])


    return vertex_by_layers


