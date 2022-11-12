from math import pi, cos, sin

from compas.numerical import fd_numpy


def smooth_mesh_fd(mesh):
    """
    Smoothen a quad mesh using the force density method.
    """
    key2index = mesh.key_index()
    index2key = mesh.index_key()

    # map boundary to circle
    fixed = [key2index[key] for key in mesh.vertices_on_boundary()[:-1]]
    n = len(fixed)

    for i, vidx in enumerate(fixed):
        vkey = index2key[vidx]
        attr = mesh.vertex[vkey]
        attr['x'] = 0.5 * cos(i / n * 2 * pi)
        attr['y'] = 0.5 * sin(i / n * 2 * pi)
        attr['z'] = 0

    # force density method
    vertices = [mesh.vertex_coordinates(vkey) for vkey in mesh.vertices()]
    edges = [(key2index[u], key2index[v]) for u, v in mesh.edges()]
    q = [1.0] * len(edges)
    loads = [[0.0, 0.0, 0.0]] * len(vertices)
    xyz, q, f, l, r = fd_numpy(vertices, edges, fixed, q, loads)

    for i, (x, y, z) in enumerate(xyz):
        vkey = index2key[i]
        attr = mesh.vertex[vkey]
        attr['x'] = x
        attr['y'] = y
        attr['z'] = z

    return mesh
