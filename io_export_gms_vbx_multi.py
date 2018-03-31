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
from os import path
from os.path import splitext
from array import *
from struct import pack, calcsize

# Conversion functions
def float_to_int(val):
    return int(val*255)

def color_to_binary(val):
    return [int(x*255) for x in reversed(val)]

def vertex_group_ids_to_bitmask(vertex):
    list = [x.group for x in vertex.groups]
    # TODO Make use of some aggregator function
    masked = 0
    for group in list:
        masked |= 1 << group
    return masked

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
def prep(context,format_options):
    # Get list of all objects
    #context.
    pass

# Latest function for getting data from each object in the scene hierarchy
# TODO: document format of return value
def get_byte_data(attribs,context):
    # Get objects
    s = context.scene
    o = context.object
    m = o.data
    
    # Get all attributes from ref, defined in attr
    # and place them at appropriate indexes in list
    def fetch_attribs(attr,ref,list):
        for attrib in attr:
            fmt = attr[attrib]['fmt']
            indices = attr[attrib]['pos']
            val = getattr(ref,attrib)
            if 'func' in attr[attrib]:
                val = attr[attrib]['func'](val)
            if len(fmt) == 1:
                val_bin = pack(fmt,val)
            else:
                val_bin = pack(fmt,*val)
            for j in indices:
                list[j] = val_bin
    
    #Get all indices in the attributes array that will contain interpolated values
    lerped_indices = [i for i,x in enumerate(attribs) if len(x) == 4 and x[3] == 'i']
    lerp_index = lerped_indices[0]          # Index of first interpolated attribute value

    # Convert linear list to nested dictionary for easier access while looping
    map_unique = {}
    
    for a in attribs:
        map_unique[a[0]] = dict()
    
    for a in attribs:
        map_unique[a[0]][a[1]]  = a[2]
        map_unique[a[0]][a[1]]['pos']  = []
    
    for i, a in enumerate(attribs):
        map_unique[a[0]][a[1]]['pos'].append(i)

    # (TODO: perform dummy pass through object data to dynamically determine format (see lines below))
    # Note: current code is sufficient at the moment
    fmt_cur = ''
    for a in attribs[:lerp_index]:      # Current attribs format
        fmt_cur += a[2]['fmt']
    fmt = ''
    for a in attribs:                   # All attribs format
        fmt += a[2]['fmt']
    fmt_cur_size = calcsize(fmt_cur)
    fmt_size = calcsize(fmt)

    # Generate list with required bytearrays for each frame (assuming triangulated faces)
    frame_count = s.frame_end-s.frame_start+1
    arr = [bytearray(fmt_size*len(m.polygons)*3) for x in range(frame_count)]

    # Init list
    list = [0 for i in attribs]

    for i in range(frame_count):
        s.frame_set(s.frame_start+i)
        
        # Make a copy of object and data to work with
        c = o.copy()
        s.objects.link(c)
        mc = c.data = o.data.copy()
        
        if 'scene' in map_unique:
            fetch_attribs(map_unique['scene'],s,list)
        
        uvs = mc.uv_layers.active.data
        
        # TODO: foreach object in selection
        
        
        # Select current object
        for k in s.objects: k.select = False
        c.select = True
        s.objects.active = c
        
        # Apply modifiers and transform
        bpy.ops.object.modifier_add(type='TRIANGULATE')
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        
        c.select = True
        
        a = 0   # Counter for offsets in bytearrays
        for p in mc.polygons:
            if 'polygon' in map_unique:
                fetch_attribs(map_unique['polygon'],p,list)
            
            if 'material' in map_unique:
                mat = mc.materials[p.material_index]
                fetch_attribs(map_unique['material'],mat,list)
                
            for li in p.loop_indices:
                # First get loop index
                loop = mc.loops[li]
                # Get vertex
                v = mc.vertices[loop.vertex_index]
                
                # Get UV
                uv = uvs[loop.index]
                if 'uv' in map_unique:
                    fetch_attribs(map_unique['uv'],uv,list)
                
                # Get vertex attributes
                if 'vertex' in map_unique:
                    fetch_attribs(map_unique['vertex'],v,list)
                
                # Now join attribute bytes together
                bytes = b''.join(list)
                # Index 'calculations'
                offset = a * fmt_size
                # Vertex format is always: current frame data, next frame data
                arr[i][offset:offset+fmt_cur_size] = bytes[:fmt_cur_size]
                arr[i-1][offset+fmt_cur_size:offset+fmt_size] = bytes[fmt_cur_size:]
                a = a + 1
        
        # Delete copies of objects and meshes
        bpy.ops.object.delete()     # Note: copied meshes still exist until reload
        
        # Select current object again
        for k in s.objects: k.select = False
        o.select = True
        s.objects.active = o
        
    return arr

# TODO: batch export objects
# vertex index goes into vertex buffer, object index goes into json file
# PRE: assuming triangulated faces
# TODO: rename to write_mesh_data??
# TODO: cleanup and make much more generic
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
    
    frame_option = EnumProperty(
        name="Frame",
        description="Which frames to export",
        items=(('cur',"Current","Export current frame only"),
               ('all',"All","Export all frames in range"),
        )
    )
    
    batch_mode = EnumProperty(
        name="Batch Mode",
        description="How to split individual object data over files",
        items=(('one',"Single File", "Batch all into a single file"),
               ('perobj',"Per Object", "Create a file for each object in the selection"),
               ('perfra',"Per Frame", "Create a file for each frame"),
               ('objfra',"Per Object Then Frame", "Create a directory for each object with a file for each frame"),
               ('fraobj',"Per Frame Then Object", "Create a directory for each frame with a file for each object"),
        )
    )
    
    format_options = EnumProperty(
        name="Format Options",
        options={'ENUM_FLAG'},
        description="Which attributes to include in format",
        items=(('pos',"Position","Include vertex position in format"),
               ('nml',"Normal","Include vertex normal in format"),
               ('clr',"Colour","Include material diffuse colour in format"),
               ('uvs',"UVs","Include all UV coordinates in format")
        )
    )
    
    vertex_groups = BoolProperty(
        name="Vertex Groups",
        description="Tag vertices with an additional vertex group attribute and add vertex group mapping to json file",
    )
    
    join_into_active = BoolProperty(
        name="Join Into Active",
        default=False,
        description="Whether to join the selection into the active object",
    )
    
    split_by_material = BoolProperty(
        name="Split By Material",
        default=False,
        description="Whether to split joined mesh by material after joining",
    )
    
    # TODO: remove this hard-coded stuff
    attribs = [
    ("vertex","co",{'fmt':'fff'}),
    ("vertex","normal",{'fmt':'fff'}),
    ("uv","uv",{'fmt':'ff'}),
    ("material","diffuse_color",{'fmt':'BBB','func':color_to_binary}),
    ("material","alpha",{'fmt':'B','func':float_to_int}),
    ("vertex","co",{'fmt':'fff'},'i'),
    ("vertex","normal",{'fmt':'fff'},'i'),
    ]

    def execute(self, context):
        result = get_byte_data(self.attribs,context)
        f = open(self.filepath,"wb")
        for a in result:
            f.write(a)
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