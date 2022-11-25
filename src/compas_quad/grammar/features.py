from collections import Counter


__all__ = ["mesh_features_topology",
           "features_key",
           "revert_features_key"]


TOPO_INDICES = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]


def mesh_features_topology(mesh):
    """
    Calculate the topological features of a quad mesh.

    The resulting feature vector is a list of length N and has this structure:

        |# vertices  # edges  # strips  # singularities  || # vertices per individual topological index || # vertices per neighborhood topological index|

    where || denotes concatenation.

    The individual and the neighborhood topological index of a vertex lies in the range [-1, 1], in 0.25 steps:

        |<-1  -1  -0.75  -0.5  -0.25  0.0  +0.25  +0.5  +0.75  +1  >+1|
    """
    topo_descriptors = ["number_of_vertices",
                        "number_of_edges",
                        "number_of_strips",
                        "number_of_singularities"]

    features = []
    for descriptor in topo_descriptors:
        features.append(getattr(mesh, descriptor)())

    for index_counter in (mesh_number_vertices_per_topo_index,
                          mesh_number_vertices_per_topo_index_neighborhood
                          ):
        counts = index_counter(mesh)
        features.extend(counts)

    return features


def mesh_number_vertices_per_topo_index(mesh):
    """
    Compute the number of vertices per each supported topological index in the mesh.

    The supported topological index of the vertices are ordered and lie in the range [-1, 1], in 0.25 steps:

        |<-1  -1  -0.75  -0.5  -0.25  0.0  +0.25  +0.5  +0.75  +1  >+1|
    """
    return histogram(data=mesh.vertices_topo_index(), bins=TOPO_INDICES)


def mesh_number_vertices_per_topo_index_neighborhood(mesh):
    """
    Compute the number of vertices per neighborhood topological index in the mesh.

    The neighbor-aggregated index of a vertex is calculated as the sum of the
    topological indices the first-ring neighbors of the vertex.

    The supported topological index of the vertices are ordered and lie in the range [-1, 1], in 0.25 steps:

        |<-1  -1  -0.75  -0.5  -0.25  0.0  +0.25  +0.5  +0.75  +1  >+1|
    """
    return histogram(data=mesh.vertices_topo_index_neighborhood(), bins=TOPO_INDICES)


def features_key(features, precision="d"):
    """
    Convert a feature vector into a string that can be hashed.
    """
    formatter = lambda x: "{0:.{1}},".format(x, precision)
    if precision == "d":
        formatter = lambda x: "{0},".format(int(x))

    return "".join(formatter(f) for f in features)[:-1]


def revert_features_key(gkey):
    """
    Revert a feature key string into xyz coordinates.
    """
    xyz = gkey.split(",")
    return [float(i) for i in xyz]


def histogram(data, bins, include_outliers=True):
    """
    Count the number of occurences per bin in the data.
    """
    counter = Counter((float(d) for d in data))

    counts = []
    for topo_index in bins:
        count = counter.get(topo_index) or 0
        counts.append(count)

    # deal with the extrema
    if include_outliers:
        count_low = 0
        count_high = 0
        for key in set(counter.keys()) - set(bins):
            if key < bins[0]:
                count_low += 1
            elif key > bins[-1]:
                count_high += 1

        counts.append(count_high)
        counts.insert(0, count_low)

    return counts
