# Conversion functions (add your own here)

# The format is as follows:
#
# function_name(value, [context], [custom_args])
#
# value is the value currently being written, e.g. the value of MeshVertex.co
# context contains references to all other sources. It contains the following: 
#
# TODO
#
# custom_args is a dictionary (map) constructed from
# the property set in the vertex attribute
#

from mathutils import *

def float_to_byte(val):
    """Convert value in range [0,1] to an integer value in range [0,255]"""
    return int(val*255)

def vec_to_bytes(val):
    """Convert a list of values in range [0,1] to a list of integer values in range [0,255]"""
    return [int(x*255) for x in val]

def invert_v(val):
    """Invert the v coordinate of a (u,v) pair"""
    return [val[0],1-val[1]]

def invert_y(val):
    """Invert the y coordinate of a vector"""
    return [val[0],-val[1],val[2]]

def vertex_group_ids_to_bitmask(vertex):
    """Return a bitmask containing the vertex groups a vertex belongs to"""
    list = [x.group for x in vertex.groups]
    masked = 0
    for group in list:
        masked |= 1 << group
    return masked

def mat_name_to_index(val):
    """Return the index of the material with the given name in bpy.data.materials"""
    return bpy.data.materials.find(val)

def dot_with_light_vector(val):
    """Return the dot product of val with a constant vector"""
    return val.dot(Vector([0, 0, 1]))

def constant_from_map(val, args):
    """Return a constant value from the custom arguments provided, val is unused"""
    return args["a"]
