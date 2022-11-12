from collections import Counter


__all__ = ["mesh_features_topology",
           "features_key",
           "revert_features_key"]


def mesh_features_topology(mesh):
    """
    Calculate the topological features of a quad mesh.

    The resulting feature vector is a list of length N and has this structure:

        |# vertices  # edges  # strips  # singularities  || # vertices per topological index|

    where || denotes concatenation.

    The supported topological index of the vertices lie in the range [-1, 1], in 0.25 steps:

        |<-1  -1  -0.75  -0.5  -0.25  0.0  +0.25  +0.5  +0.75  +1  >+1|
    """
    topo_descriptors = ["number_of_vertices",
                        "number_of_edges",
                        "number_of_strips",
                        "number_of_singularities"]

    features = []
    for descriptor in topo_descriptors:
        features.append(getattr(mesh, descriptor)())

    counts = mesh_number_vertices_per_topo_index(mesh)
    features.extend(counts)

    return features


def mesh_number_vertices_per_topo_index(mesh):
    """
    Compute the number of vertices per each supported topological index in the mesh.

    The supported topological index of the vertices are ordered and lie in the range [-1, 1], in 0.25 steps:

        |<-1  -1  -0.75  -0.5  -0.25  0.0  +0.25  +0.5  +0.75  +1  >+1|
    """
    topo_indices = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]

    counter = Counter((float(index) for index in mesh.vertices_topo_index()))

    counts = []
    for topo_index in topo_indices:
        count = counter.get(topo_index) or 0
        counts.append(count)

    # deal with the extrema
    count_low = 0
    count_high = 0
    for key in set(counter.keys()) - set(topo_indices):
        if key < topo_indices[0]:
            count_low += 1
        elif key > topo_indices[-1]:
            count_high += 1

    counts.append(count_high)
    counts.insert(0, count_low)

    return counts


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


if __name__ == "__main__":
    features = [10, 4, 8, 6, 5, 2, 0, -1]
    key = feature_key(features, precision='d')
    print(key)
    print(revert_feature_key(feature_key(features)))
