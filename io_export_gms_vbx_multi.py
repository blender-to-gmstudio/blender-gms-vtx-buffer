bl_info = {
    "name": "Export GM:Studio MultiTexture",
    "description": "Export the current scene to a buffer that can be loaded in GM:Studio",
    "author": "Bart Teunis",
    "version": (1, 0, 0),
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

# First preparations
def prepare_selection():
    bpy.ops.object.duplicates_make_real()
    bpy.ops.object.make_local(type='SELECT_OBDATA') # TODO: also MATERIAL??
    bpy.ops.object.make_single_user(object=True,obdata=True,material=False,texture=False,animation=False)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.ops.object.convert(target='MESH')

# Prepare vertex formats and object mappings
def prep():
    pass

# The final function for the basic loop!
def export():
    # First things first: prepare selection (import from libraries, make duplis real, etc, ...
    prepare_selection()

from array import *
from struct import pack
from os.path import splitext
import json
import bpy

#import logging

# Return an array containing mesh data according to the given format
# Append interpolation values when a second mesh is provided
# PRE: vertex indices (actually loop indices) need to correspond between meshes
# PRE: mesh should be triangulated
def mesh_data_to_bytearray(format,added_vtx_info,mesh1,mesh2=None):
    vertex_data = array('B')
    
    uvs = mesh1.uv_layers.active.data if len(mesh1.uv_layers) > 0 else None
    
    # Loop per vertex
    for loop in mesh1.loops:
        # Get the face corresponding to the loop
        face = mesh1.polygons[loop.index // 3]                      # Assuming triangulated faces!
        mat  = mesh1.materials[face.material_index] if len(mesh1.materials) > 0 else None
        vtx  = mesh1.vertices[loop.vertex_index]
        pos = vtx.co
        nml = vtx.normal
        col = [int(x) for x in mat.diffuse_color*255] if mat != None else [255,255,255]
        col.reverse()                                               #bgr
        a = mat.alpha*255
        uv = uvs[loop.index].uv[:] if uvs != None else (0,0)
        
        # Current frame vertex data
        for attrib in format:
           if attrib == 'Pos':
               # in_Position (x,y,z)
                vertex_data.extend(pack('fff',*pos))
           elif attrib == 'Normal':
               # in_Normal (x,y,z)
               vertex_data.extend(pack('fff',*nml))
           elif attrib == 'Colour':
               # in_Colour (r,g,b,a)
               vertex_data.extend(pack('BBB',*col))                     #bgr
           elif attrib == 'Alpha':
                # Alpha
               vertex_data.extend(pack('B',a))                          #a
           elif attrib == 'Textcoord':
               # in_TextureCoord (u,v)
               vertex_data.extend(pack('ff',*uv))                       # Invert y textcoord
        
        # Next frame vertex data
        if mesh2 != None:
            face = mesh2.polygons[loop.index // 3]                      # Assuming triangulated faces!
            vtx = mesh2.vertices[loop.vertex_index]
            pos = vtx.co
            nml = vtx.normal
            
            for attrib in format:
                if attrib == 'Pos':
                    vertex_data.extend(pack('fff',*pos))
                elif attrib == 'Normal':
                    vertex_data.extend(pack('fff',*nml))
        
        # Append additional vertex info provided by the caller
        vertex_data.extend(added_vtx_info)
        
    return vertex_data

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

# << Existing functionality from previous morph exporter - to be fully reworked >>
# The core loop is important
def write_vtx_buffer(context, filepath, caller):
    # Easier names
    s = context.scene
    
    # Remember selection
    selection = context.selected_objects
    active = context.active_object
    
    # Consider only supported object types
    working_selection = context.selected_objects if caller.selection_only else context.scene.objects
    working_selection = [x for x in working_selection if x.type in {'MESH'}]    # TODO: support 'EMPTY' with duplis
    
    # Check if working selection contains objects, cancel if not
    if len(working_selection) == 0:
        return {'CANCELLED'}
    
    # Open files
    f_data = open(filepath, 'wb')
    
    # Retrieve vertex format (attributes must be in order!)
    vertex_format = caller.vertex_format.split(',')
    
    # Initialize some stuff
    b = working_selection[0]
    old_frame = s.frame_current
    
    frame_range = range(s.frame_start,s.frame_end+1)
    no_frames = len(frame_range)
    
    # Reset working selection
    for obj in s.objects:
        obj.select = True if obj in working_selection else False
    s.objects.active = b
    
    s.frame_set(s.frame_start)
    
    # Generate first frame's 'current' mesh
    make_merged_copy(context)
    obj_cur = context.active_object                 # Result is now available in context.active_object
    obj_nxt = None
    
    i = 0   # Frame index in vertex buffer
    for frame in frame_range:
        # Initialize
        additional_vertex_info = array('B')
        additional_vertex_info.extend(pack('f',i))
        i += 1
        
        # Calculate and set next frame to be generated
        frame_next = frame % no_frames
        s.frame_set(frame_next)
        
        # Reset working selection
        for obj in s.objects:
            obj.select = True if obj in working_selection else False
        s.objects.active = b
        
        make_merged_copy(context)
        obj_nxt = context.active_object             # Result is now available in context.active_object
        
        # TODO: set object origin to (0,0,0) to allow easy scaling, scale y by -1 and flip normals
        #context.scene.cursor_location = [0,0,0]
        #bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        # Write current frame
        data = mesh_data_to_bytearray(vertex_format,additional_vertex_info,obj_cur.data,obj_nxt.data) # mesh_cur and mesh_nxt should have identical loop indices and originate from the same joined meshes
        data.tofile(f_data)
        
        # Delete current joined object
        bpy.ops.object.select_pattern(pattern=obj_cur.name,extend=False)
        bpy.ops.object.delete()
        
        # Make 'cur' reference the 'nxt' frame data (this frame's next is next frame's current)
        obj_cur = obj_nxt
    
    # Delete last joined object
    bpy.ops.object.select_pattern(pattern=obj_nxt.name,extend=False)
    bpy.ops.object.delete()
    
    # Restore current frame
    s.frame_set(old_frame)
    
    # Restore selection and active
    for obj in selection:
        obj.select = True
    s.objects.active = active
    
    f_data.close()
    
    return {'FINISHED'}

# TODO: replace with improved function prepare_selection()
def make_merged_copy(context):
    # TODO: select a root object to prevent wrong joins => much simpler: join to active object!
    # Active object therefore must be a root object!
    # TODO: add dupli support
    
    # This one is tricky
    # When we join the exact same selection of objects in the exact same way, 
    # we get meshes that have the same loop indices between frames
    # This allows us to loop through the mesh's loops
    # For a detailed background, see: https://wiki.blender.org/index.php/Dev:Source/Modeling/BMesh/Design#The_Loop_Cycle:_A_circle_of_face_edges_around_a_polygon.
    
    # Put all into a single mesh
    bpy.ops.object.duplicate()                      # Duplicate selection, newly created duplicated objects become the new selection
    #bpy.ops.object.duplicates_make_real()           # Make duplicates real (TESTING)
    bpy.ops.object.convert(target='MESH')           # Convert to mesh, applying modifiers
    bpy.ops.object.join()                           # Create a single mesh
    
    #bpy.ops.object.select_hierarchy()
    bpy.ops.object.modifier_add(type='TRIANGULATE') # Add triangulate modifier to joined mesh (!)
    bpy.ops.object.convert(target='MESH')           # Convert to mesh, applying modifiers
    
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
    context.active_object.animation_data_clear()    # Clear, since animation gets baked into mesh

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