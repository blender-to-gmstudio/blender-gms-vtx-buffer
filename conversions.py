# Conversion functions (add your own here)

# The format is as follows:
#
# function_name(value, [ctx], [args])
#
# value is the value currently being written, e.g. the value of MeshVertex.co
# ctx contains references to all other sources. It contains the following: 
#
# ctx["scene"]: a reference to the current scene being exported
# ctx["object"]: a reference to the object currently being exported
# ctx["polygon"]: a reference to the polygon currently being exported
# ctx["loop"]: a reference to the loop currently being exported
#
# args is a dictionary (map) constructed from
# the property set in the vertex attribute
# This should be a valid JSON string
#

from mathutils import *

def float_to_byte(val, ctx=None):
    """Convert value in range [0,1] to an integer value in range [0,255]"""
    return int(val*255)

def vec_to_bytes(val, ctx=None):
    """Convert a list of values in range [0,1] to a list of integer values in range [0,255]"""
    return [int(x*255) for x in val]

def invert_v(val, ctx=None):
    """Invert the v coordinate of a (u,v) pair"""
    return [val[0],1-val[1]]

def invert_y(val, ctx=None):
    """Invert the y coordinate of a vector"""
    return [val[0],-val[1],val[2]]

def vertex_group_ids_to_bitmask(vertex, ctx=None):
    """Return a bitmask containing the vertex groups a vertex belongs to"""
    list = [x.group for x in vertex.groups]
    masked = 0
    for group in list:
        masked |= 1 << group
    return masked

def mat_name_to_index(val, ctx=None):
    """Return the index of the material with the given name in bpy.data.materials"""
    return bpy.data.materials.find(val)

def dot_with_light_vector(val, ctx=None):
    """Return the dot product of val with a constant vector"""
    return val.dot(Vector([0, 0, 1]))

def constant_from_map(val, ctx=None, args={}):
    """Return a constant value from the custom arguments provided, val is unused"""
    return args["a"]

def value_from_context(val, ctx):
    """Return the current frame in the scene as an example"""
    return ctx["scene"].frame_current
