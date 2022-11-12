import os

from collections import defaultdict
from collections import Counter

from time import time

from tqdm import tqdm

from compas.colors import Color
from compas.geometry import Point

from compas_plotters import Plotter

from compas_quad.datastructures import CoarseQuadMesh

from compas_quad.grammar import Lizard
from compas_quad.grammar import string_generation_brute
from compas_quad.grammar import string_generation_random
from compas_quad.grammar import string_generation_structured
from compas_quad.grammar import string_generation_markov
from compas_quad.grammar import string_generation_markov_budget

from compas_quad.grammar import mesh_features_topology
from compas_quad.grammar import features_key

from lizard_postprocess import smooth_mesh_fd


# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# I/O
postprocess = True
plot = True
export = False
filepath_plot = "/Users/arpj/Desktop/patterns.pdf"

in_mesh_refinement = 2  # densify the input 1-face quad mesh
out_mesh_refinement = 3  # densify the ouput quad mesh

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
random_string_seed = 43
random_string_number = 100
random_string_length = 10
random_string_ratios = [0.2, 0.5, 0.3]

# for 'structured' construction
add_structured_strings = False
structured_string_seed = 43
structured_string_characters = 'atp'
structured_string_number = 1000
structured_string_length = 10

# for 'markovian' construction
add_markov_strings = False
markov_string_seed = 43
markov_string_characters = 'atp'
markov_string_number = 100
markov_string_length = 10
# starting probabilities for a, t, p
# if set to None, it will be calculated automatically as the
# stationary distribution of the Markov chain
# markov_p_init = [0.7, 0.15, 0.15]
markov_p_init = None
# probability transition matrix from one state to another
# rows represent the states at step t, and colums at step t+1
# |A to A    A to T    A to P|
# |T to A    T to T    T to P|
# |P to A    P to T    P to P|
markov_p_transition = [[0.2, 0.4, 0.4],
                       [0.2, 0.4, 0.4],
                       [0.2, 0.4, 0.4]]

# for 'budgeted markovian' construction
add_markov_budget_strings = True
markov_budget_string_characters = 'tp'
markov_budget_sentences_number = 10000
markov_budget_words_number = 3
markov_budget_characters_number = 10
# starting probabilities for t, p
# if set to None, it will be calculated automatically as the
# stationary distribution of the Markov chain
# probability transition matrix from one state to another
# rows represent the states at step t, and colums at step t+1
# |T to T    T to P|
# |P to T    P to P|
markov_budget_string_seed = 43
markov_budget_p_init = [0.45, 0.45, 0.0]
markov_budget_p_transition = [[0.6, 0.4],
                              [0.4, 0.6]]


# markov_budget_p_init = [0.45, 0.45, 0.0]
# probability transition matrix from one state to another
# rows represent the states at step t, and colums at step t+1
# |T to T    T to P    T to S|
# |P to T    P to P    P to S|
# markov_budget_p_transition = [[0.5, 0.3, 0.2],
#                               [0.3, 0.5, 0.2]]

# visualization
edgecolor = Color.black()
facecolor = Color.grey().lightened(80)

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

### intialise ###

# dummy mesh
vertices = [[0.5, 0.5, 0.0],
            [-0.5, 0.5, 0.0],
            [-0.5, -0.5, 0.0],
            [0.5, -0.5, 0.0]]

faces = [[0, 1, 2, 3]]
coarse = CoarseQuadMesh.from_vertices_and_faces(vertices, faces)

# denser mesh
coarse.collect_strips()
coarse.strips_density(in_mesh_refinement)
coarse.densification()
mesh0 = coarse.dense_mesh()
mesh0.collect_strips()
num_boundaries_init = len(mesh0.vertices_on_boundaries())

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# position marker
for u, v in mesh0.edges_on_boundary():
    if mesh0.vertex_degree(u) == 2:
        tail, head = u, v
        break
    elif mesh0.vertex_degree(v) == 2:
        tail, head = v, u
        break

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# produce strings
strings = []

if add_given_strings:
    strings += given_strings

if add_brute_strings:
    print("Generating strings by enumeration")
    strings += list(string_generation_brute(brute_string_characters,
                                            brute_string_length))

if add_random_strings:
    print("Generating random strings")
    strings += list(string_generation_random(random_string_characters,
                                             random_string_number,
                                             random_string_length,
                                             ratios=random_string_ratios,
                                             seed=random_string_seed))

if add_structured_strings:
    print("Generating structured strings")
    strings += list(string_generation_structured(structured_string_characters,
                                                 structured_string_number,
                                                 structured_string_length,
                                                 structured_string_seed))

if add_markov_strings:
    print("Generating Markov strings")
    strings += list(string_generation_markov(markov_string_characters,
                                             markov_string_number,
                                             markov_string_length,
                                             markov_p_init,
                                             markov_p_transition,
                                             markov_string_seed))

if add_markov_budget_strings:
    print("Generating Markov strings with a budget")
    strings += list(string_generation_markov_budget(markov_budget_string_characters,
                                                    markov_budget_sentences_number,
                                                    markov_budget_words_number,
                                                    markov_budget_characters_number,
                                                    markov_budget_p_init,
                                                    markov_budget_p_transition,
                                                    markov_budget_string_seed))

unique_strings = set(strings)
number_strings = len(strings)
number_unique_strings = len(unique_strings)

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# String to mesh
meshes = []
successful_strings = []
failed_strings = []

num_fail_lizard = 0
num_fail_unify = 0

print("\nTransforming strings to meshes")

t0 = time()
### lizard - let's grooow! ###
for string in tqdm(unique_strings):

    # modifiy topology
    mesh = mesh0.copy()
    lizard = Lizard(mesh)
    lizard.init(tail=tail, head=head)

    try:
        lizard.from_string_to_rules(string)
    except:
        failed_strings.append(string)
        num_fail_lizard += 1
        continue

    try:
        mesh.unify_cycles()
    except:
        failed_strings.append(string)
        num_fail_unify += 1
        continue

    meshes.append(mesh.copy())
    successful_strings.append(string)


number_successful_strings = len(successful_strings)
num_lizard_strings = len(successful_strings)
number_failed_strings = len(failed_strings)

print(f'Lizard time {round(time() - t0, 3)}s\n')

# sanity checks
assert len(meshes) == len(successful_strings)
msg = f'{number_successful_strings} success, {number_failed_strings} fail, {number_unique_strings} total unique'
assert number_successful_strings + number_failed_strings == number_unique_strings, msg

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

featkey_stringmesh = defaultdict(dict)

for string, mesh in zip(successful_strings, meshes):
    features = mesh_features_topology(mesh)
    featkey_stringmesh[features_key(features, precision="d")][string] = mesh

number_unique_meshes_pre = len(featkey_stringmesh)

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# Geometrical processing
num_fail_smooth = 0
num_fail_manifold = 0
num_fail_boundarychange = 0

deletable_featkeys = []

if postprocess:
    print("\nPost-processing meshes")
    t0 = time()

    for featkey, stringmesh in tqdm(featkey_stringmesh.items(), total=len(featkey_stringmesh)):
        deletable = []
        for string, mesh in stringmesh.items():

            mesh = mesh.copy()

            try:
                mesh = smooth_mesh_fd(mesh)
                mesh = CoarseQuadMesh.from_vertices_and_faces(*mesh.to_vertices_and_faces())
                mesh.collect_strips()
                mesh.strips_density(out_mesh_refinement)
                mesh.densification()
                mesh = mesh.dense_mesh()
                mesh = smooth_mesh_fd(mesh)

            except:
                num_fail_smooth += 1
                deletable.append(string)
                continue

            # TODO: fix lizard to avoid non-manifoldness
            # manifoldness
            if not mesh.is_manifold():
                num_fail_manifold += 1
                deletable.append(string)
                continue

            # discard meshes with internal holes
            if len(mesh.vertices_on_boundaries()) > num_boundaries_init:
                num_fail_boundarychange += 1
                deletable.append(string)
                continue

            # only after all tests pass, count and append post-processed mesh
            stringmesh[string] = mesh

        # delete entries that failed
        for dstring in deletable:
            del stringmesh[dstring]

        if len(stringmesh) < 1:
            deletable_featkeys.append(featkey)

    print(f'Post-processing time {round(time() - t0, 3)}s\n')

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

num_fail_duplicated = num_lizard_strings - number_unique_meshes_pre

for featkey in deletable_featkeys:
    del featkey_stringmesh[featkey]

number_unique_meshes = len(featkey_stringmesh)

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# results
print(f'\nGenerated strings: {number_strings}')
print(f'Unique strings: {round(100 * number_unique_strings / number_strings, 2)}% [{number_unique_strings} / {number_strings} generated strings]')
print('Lizard meshes: {}% [{} / {} unique strings]'.format(
    round(100 * number_successful_strings / number_unique_strings, 2),
    number_successful_strings,
    number_unique_strings))
print('Unique meshes: {}% [{} / {} unique strings]'.format(
    round(100 * number_unique_meshes_pre / number_unique_strings, 2),
    number_unique_meshes_pre,
    number_unique_strings))
print('Post-processed meshes: {}% [{} / {} unique strings]'.format(
    round(100 * number_unique_meshes / number_unique_strings, 2),
    number_unique_meshes,
    number_unique_strings))

nums_fail = [num_fail_lizard, num_fail_unify, num_fail_duplicated, num_fail_smooth, num_fail_manifold, num_fail_boundarychange]

nums_fail_2 = [sum(nums_fail)] + nums_fail
failure_ratios = [round(100 * f / number_unique_strings, 2) for f in nums_fail_2]
print('\nUnsuccessful meshes: {}% [Lizard {}%  Unify {}% | Duplicated meshes: {}% | Smoothing {}%  Non-manifold {}%  Boundaries {}%]'.format(*failure_ratios))

# TODO: Fix assertion
# assert sum(nums_fail) + number_unique_meshes == number_unique_strings, f"{sum(nums_fail)} + {number_unique_meshes} vs. {number_unique_strings}"

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

# export
if export:
    HERE = os.path.dirname(__file__)
    for mesh, string in zip(meshes, successful_strings):
        FILE = os.path.join(HERE, 'data/{}_{}.json'.format(in_mesh_refinement, string))
        mesh.to_json(FILE)

# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

if plot:
    print("\nPlotting")

    plotter = Plotter(figsize=(16, 9), dpi=200)

    n = number_unique_meshes
    for k, (featkey, stringmesh) in tqdm(enumerate(featkey_stringmesh.items()),
                                         total=number_unique_meshes):

        meshes = list(stringmesh.values())
        if len(meshes) < 1:
            continue
        mesh = meshes[0]  # take the first mesh

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
        for vkey in mesh.singularities():
            plotter.add(Point(*mesh.vertex_coordinates(vkey)),
                        size=4,
                        # edgecolor=None,
                        facecolor=Color.magenta())

    print("Zooming in...")
    plotter.zoom_extents()
    print("Saving...")
    plotter.save(filepath_plot)

print("\nDone!")
