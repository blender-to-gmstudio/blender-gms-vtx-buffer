# This file contains functionality for a basic export to glTF v2
import bpy

from struct import calcsize

# Constant definitions, etc.
NumComponentsToAccessorTypeMap = {
    1: 'SCALAR',
    2: 'VEC2',
    3: 'VEC3',
    4: 'VEC4',
    #'MAT2': 4, # Let's assume for now we'll never use this => unique mapping!
    9: 'MAT3',
    16: 'MAT4',
}

componentTypeMap = {
    'b': 5120,
    'B': 5121,
    'f': 5126,
}

def accessors(mesh, bufferView, vertex_format):
    """Get a glTF accessor description from the given vertex format"""
    
    # Example: passthrough format descriptor
    """
    fmt = [
        {"name":"","fmt":"fff","int":0,"func":'invert_y',"args":'',"datapath":[{"name":'',"node":'MeshVertex'},{"name":'',"node":"co"}]},
        {"name":"","fmt":"BBBB","int":0,"func":'vec_to_bytes',"args":'',"datapath":[{"name":'',"node":'Material'},{"name":'',"node":"diffuse_color"}]},
        {"name":"","fmt":"ff","int":0,"func":'none',"args":'',"datapath":[{"name":'',"node":'MeshUVLoop'},{"name":'',"node":"uv"}]},
    ]
    """
    
    desc = []
    byteOffset = 0
    for attrib in vertex_format:
        componentType = componentTypeMap[attrib["fmt"][0]]
        numComponents = len(attrib["fmt"])
        
        desc.append({
            "byteOffset": byteOffset,
            "bufferView": bufferView,
            "count": len(mesh.loops),       # Assuming triangulated mesh
            "componentType": componentType,
            "type": NumComponentsToAccessorTypeMap[numComponents],
        })
        byteOffset = byteOffset + calcsize(attrib["fmt"])
    
    return desc

def generate_glTFv2():
    """Main entry point for the export"""
    gltf_json = {
        "asset": {
            "version": "2.0",
            "generator": "Blender2GM:Studio",
        },
        "buffers": [
            {
                "byteLength": 1024,
                "uri": "data.bin"
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteLength": 512,
                "byteOffset": 0
            }
        ],
        "nodes": [
            {
                "name": "RootNode"
            }
        ],
        "scenes": {
            {
                "name": "Scene",
                "nodes": [
                    0
                ]
            }
        },
        "scene": 0,
        "meshes": [
            {
                "primitives": [
                    {
                        
                    }
                ]
            }
        ]
    }
    
    return gltf_json