import os
from math import pi, cos, sin

from time import time

from tqdm import tqdm

from compas.colors import Color
from compas.geometry import Point

from compas_quad.datastructures import CoarseQuadMesh

from compas_quad.grammar import Lizard
from compas_quad.grammar import string_generation_brute
from compas_quad.grammar import string_generation_random
from compas_quad.grammar import string_generation_structured

from compas.numerical import fd_numpy

from compas_plotters import Plotter


def postprocessing(mesh):

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


### parameters ###
in_mesh_refinement = 2  # densify the input 1-face quad mesh
out_mesh_refinement = 4  # densify the ouput quad mesh

# for 'given' production (try: ata, attta, d, atttad, attpptta ...)
add_given_strings = False
given_strings = ['attta']

# for 'brute' force enumeration
add_brute_strings = False
brute_string_characters = 'atp'
brute_string_length = 10

# for 'random' generation
add_random_strings = False
random_string_characters = 'atp'
random_string_seed = 29
random_string_number = 100
random_string_length = 10
random_string_ratios = [0.2, 0.5, 0.3]

# for 'structured' construction
add_structured_strings = True
structured_string_seed = 29
structured_string_characters = 'atp'
structured_string_number = 200
structured_string_length = 10

edgecolor = Color.black()
facecolor = Color.grey().lightened(80)

postprocess = True
plot = True
export = False

filepath_plot = "/Users/arpj/Desktop/patterns.pdf"

### intialise ###

# dummy mesh
vertices = [[0.5, 0.5, 0.0], [-0.5, 0.5, 0.0],
            [-0.5, -0.5, 0.0], [0.5, -0.5, 0.0]]
faces = [[0, 1, 2, 3]]
coarse = CoarseQuadMesh.from_vertices_and_faces(vertices, faces)

# denser mesh
coarse.collect_strips()
coarse.strips_density(in_mesh_refinement)
coarse.densification()
mesh0 = coarse.dense_mesh()
mesh0.collect_strips()
num_boundaries_init = len(mesh0.vertices_on_boundaries())

### lizard - let's grooow! ###

# position marker
for u, v in mesh0.edges_on_boundary():
    if mesh0.vertex_degree(u) == 2:
        tail, head = u, v
        break
    elif mesh0.vertex_degree(v) == 2:
        tail, head = v, u
        break

# produce strings

strings = []

if add_given_strings:
    strings += given_strings

if add_brute_strings:
    strings += list(string_generation_brute(brute_string_characters,
                                            brute_string_length))

if add_random_strings:
    strings += list(string_generation_random(random_string_characters,
                                             random_string_number,
                                             random_string_length,
                                             ratios=random_string_ratios,
                                             seed=random_string_seed))

if add_structured_strings:
    strings += list(string_generation_structured(structured_string_characters,
                                                 structured_string_number,
                                                 structured_string_length,
                                                 structured_string_seed))

number_strings = len(strings)
print('strings {}'.format(strings))

# apply

t0 = time()
meshes = []
successful_strings, failed_strings = [], []

print("\nTransforming strings to meshes")
for k, string in enumerate(tqdm(strings)):

    # print()
    # modifiy topology
    mesh = mesh0.copy()
    lizard = Lizard(mesh)
    lizard.init(tail=tail, head=head)
    try:
        lizard.from_string_to_rules(string)
        # print("Happy lizard")
        mesh.unify_cycles()
        # print("Unified cycles")

        # export
        if export:
            HERE = os.path.dirname(__file__)
            FILE = os.path.join(HERE, 'data/{}_{}.json'.format(in_mesh_refinement, string))
            mesh.to_json(FILE)

        # geometrical processing
        if postprocess:
            mesh = postprocessing(mesh)
            mesh = CoarseQuadMesh.from_vertices_and_faces(*mesh.to_vertices_and_faces())
            mesh.collect_strips()
            mesh.strips_density(out_mesh_refinement)
            mesh.densification()
            mesh = mesh.dense_mesh()
            mesh = postprocessing(mesh)

            # TODO: fix lizard to avoid non-manifoldness
            # manifoldness
            if not mesh.is_manifold():
                print("not manifold, dude!")
                continue

            # discard meshes with internal holes
            if len(mesh.vertices_on_boundaries()) > num_boundaries_init:
                print("Number of boundaries changed. Skipping lizard walk.")
                continue

            # print("post-processed!")
        meshes.append(mesh.copy())
        successful_strings.append(string)

    except:
        failed_strings.append(string)

# results

t1 = time()
print('computation time {}s'.format(round(t1 - t0, 3)))

print('{} / {} successes ({} ratio)'.format(int(len(successful_strings)),
                                            int(number_strings), round(len(successful_strings) / number_strings, 2)))

if plot:

    print("\nPlotting")

    plotter = Plotter(figsize=(16, 9), dpi=200)

    n = len(meshes)
    for k, mesh in enumerate(tqdm(meshes)):

        # add mesh to viewer
        n2 = int(n ** 0.5)
        i = int(k / n2)
        j = int(k % n2)
        mesh.move([1.5 * (i + 1), 1.5 * (j + 1), 0.0])

        plotter.add(mesh,
                    show_vertices=False,
                    show_faces=True,
                    edgewidth=0.7,
                    edgecolor={edge: edgecolor for edge in mesh.edges()},
                    facecolor={face: facecolor for face in mesh.faces()})

        # add singularities to viewer
        for vkey in mesh.vertices():
            if mesh.is_vertex_singular(vkey):
                plotter.add(Point(*mesh.vertex_coordinates(vkey)),
                            size=4,
                            # edgecolor=None,
                            facecolor=Color.magenta())

    print("Zooming in...")
    plotter.zoom_extents()
    print("Saving...")
    plotter.save(filepath_plot)

print("Done!")
