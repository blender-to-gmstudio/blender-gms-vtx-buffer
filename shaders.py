import bpy

# Some definitions
TEMP_MAT_NAME = "Temporary Material"
SUPPORTED_SHADERNODE_INPUT_DATA_TYPES = ('VALUE', 'INT', 'BOOLEAN', 'VECTOR', 'ROTATION', 'RGBA')

# Modified workaround to get shader inputs based on answer provided here: 
# https://blender.stackexchange.com/a/254595
# 
def get_shader_nodes_inputs():
    """Get all inputs of all supported shader nodes"""
    
    prefix = 'ShaderNode'
    excluded = (prefix, 'ShaderNodeCustomGroup', 'ShaderNodeTree', 'ShaderNodeAddShader', ' ShaderNodeGroup', 'ShaderNodeScript', 'ShaderNodeOutputMaterial')
    names = [n for n in dir(bpy.types) if n.startswith(prefix) and n not in excluded]

    temp_mat = bpy.data.materials.get(TEMP_MAT_NAME)
    if not temp_mat:
        temp_mat = bpy.data.materials.new(TEMP_MAT_NAME)
        
    temp_mat.use_nodes = True
    nodes = temp_mat.node_tree.nodes

    out = dict()

    for name in names:
        nodes.clear()
        n = nodes.new(name)
        socket_to_dict = lambda s: (s.name, s.name, s.description)
        inputs = [socket_to_dict(i) for i in n.inputs if i.type in SUPPORTED_SHADERNODE_INPUT_DATA_TYPES]

        # Don't return nodes that have no inputs
        if len(inputs) == 0:
            continue

        out[name] = inputs
        
    nodes.clear()
    bpy.data.materials.remove(temp_mat)

    return out

def get_shader_input_attr(shader_node_subclass, input_name, attr_name):
    """A 'getattr' for shader nodes

    shader_node_subclass: One of the subclasses of: https://docs.blender.org/api/current/bpy.types.ShaderNode.html
    input_name: the input on which to look up the attribute
    attr_name: the name of the attribute to look up

    """

    # Create a "dummy" material on which we can lookup inputs
    temp_mat = bpy.data.materials.get(TEMP_MAT_NAME)
    if not temp_mat:
        temp_mat = bpy.data.materials.new(TEMP_MAT_NAME)
        
    temp_mat.use_nodes = True
    nodes = temp_mat.node_tree.nodes
    n = nodes.new(shader_node_subclass)

    result = getattr(n.inputs[input_name], attr_name)

    nodes.clear()
    bpy.data.materials.remove(temp_mat)

    return result
