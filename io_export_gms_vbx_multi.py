bl_info = {
    "name": "Export GM:Studio MultiTexture",
    "description": "Export the current scene to a buffer that can be loaded in GM:Studio",
    "author": "Bart Teunis",
    "version": (2, 0, 0),
    "blender": (2, 78, 0),
    "location": "File > Export",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Import-Export"}

import bpy
import shutil   # for image file copy
import json
import os
from array import *
from os import path
from struct import pack

# TODO: batch export objects
# vertex index goes into vertex buffer, object index goes into json file
# PRE: assuming triangulated faces
# TODO: rename to write_mesh_data??
def get_object_data(object, filepath):
    m = object.data
    
    fname = path.basename(filepath)
    
    batches = []
    offset = 0
    data = array('B')
    for i in range(0,len(m.materials)):
        mat = m.materials[i]                                    # Actual material object
        tris = [x for x in m.polygons if x.material_index == i] # All triangles using this material slot
        
        if (len(tris) == 0):                                    # Don't include! => results in buffer error in GM
            continue
        
        tex_slot = mat.texture_slots[0]                         # Texture must be present in slot 0
        tex = tex_slot.texture
        image = tex.image
        image.save_render(path.dirname(filepath)+os.sep+image.name)# Works for a simple file save
        if tex_slot.uv_layer == '':
            uv_layer = m.uv_layers.active
        else:
            uv_layer = m.uv_layers[tex_slot.uv_layer]
        
        batches.append({
            "offset": len(data),
            "num_verts": len(tris)*3,
            "texture"  : image.name,                            # TODO: implement map in GM!
            "use_transparency": mat.use_transparency,           # Use this for translucent materials
        })
        
        for tri in tris:
            for li in reversed(tri.loop_indices):
                vtx_index = m.loops[li].vertex_index
                vtx = m.vertices[vtx_index]
                
                data.extend(pack('fff',*vtx.co))
                data.extend(pack('fff',*tri.normal))            # Use triangle normal! (BUG: do use vertex normal??)
                data.extend(pack('ff',*(uv_layer.data[li].uv)))
                # TODO: extend with vertex group index!

    result = {"batches": batches, "geometry": fname}            # Build JSON object
    
    return (data, result)


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportGMSMultiTex(Operator, ExportHelper):
    """Export the current scene to a vertex buffer, including textures and a description file"""
    bl_idname = "export_scene.gms_multitex"  # important since its how bpy.ops.export_scene.gms_multitex is constructed
    bl_label = "Export GM:Studio Buffer MultiTexture"
    bl_options = {'PRESET'}

    # ExportHelper mixin class uses this
    filename_ext = ".vbx"

    filter_glob = StringProperty(
        default="*.vbx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    selection_only = BoolProperty(
        name="Selection Only",
        default=True,
        description="Only export objects that are currently selected",
    )
    
    visible_layers = BoolProperty(
        name="Visible Layers",
        default=True,
        description="Export selection on currently visible layers",
    )
    
    vertex_groups = BoolProperty(
        name="Vertex Groups",
        description="Tag vertices with an additional vertex group attribute and add vertex group mapping to json file",
    )
    
    batch_mode = EnumProperty(
        name="Batch Mode",
        description="How to split individual object data over files",
        items=(('Single',"Single File", "Batch all into a single file"),
               ('Object',"One File Per Object", "Create a file for each object in the selection"),
        )
    )

    def execute(self, context):
        f = open(self.filepath,"wb")
        
        objects = []
        offset = 0
        for o in context.selected_objects: 
            data, result = get_object_data(o, self.filepath)
            transform = {"location":o.location[:], "rotation_euler":o.rotation_euler[:], "scale":o.scale[:]}
            objects.append({"name":o.name, "transform":transform, "data":result, "offset":offset})
            offset = offset + len(data)
            data.tofile(f)
        
        f.close()
        
        json_fname = os.path.splitext(self.filepath)[0]+'.json'
        f = open(json_fname,"w")
        json.dump(objects,f)
        f.close()
        
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportGMSMultiTex.bl_idname, text="GM:Studio MultiTexture (*.vbx)")


def register():
    bpy.utils.register_class(ExportGMSMultiTex)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportGMSMultiTex)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()