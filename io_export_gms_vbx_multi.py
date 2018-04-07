bl_info = {
    "name": "Export GM:Studio MultiTexture",
    "description": "Export (part of) the current scene to a buffer that can be loaded in GM:Studio",
    "author": "Bart Teunis",
    "version": (0, 5, 0),
    "blender": (2, 78, 0),
    "location": "File > Export",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Import-Export"}

# Required imports
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator, PropertyGroup
import bpy
import shutil                       # for image file copy
import json
from os import path
from os.path import splitext
from struct import pack, calcsize

# Conversion functions (go into the globals() dictionary for now...)
def float_to_byte(val):
    """Convert value in range [0,1] to an integer value in range [0,255]"""
    return int(val*255)

def vec_to_bytes(val):
    """Convert a list of values in range [0,1] to a list of integer values in range [0,255]"""
    return [int(x*255) for x in reversed(val)]

def vertex_group_ids_to_bitmask(vertex):
    list = [x.group for x in vertex.groups]
    masked = 0
    for group in list:
        masked |= 1 << group
    return masked

# Latest function for getting data from each object in the scene hierarchy
# Format of return value is: [{'obj1':bytearray,'obj2':bytearray},{'obj1':bytearray,'obj2':bytearray}]
# (swap obj and frame to toggle between frame-first and object-first)
def get_byte_data(self,attribs,context):
    # Get objects
    s = context.scene
    
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
    lerp_start = lerped_indices[0] if len(lerped_indices) > 0 else len(lerped_indices)  # Index of first interpolated attribute value

    # Convert linear list to nested dictionary for easier access while looping
    # TODO: clean this up!
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
    for a in attribs[:lerp_start]:      # Current attribs format
        fmt_cur += a[2]['fmt']
    fmt = ''
    for a in attribs:                   # All attribs format
        fmt += a[2]['fmt']
    fmt_cur_size = calcsize(fmt_cur)
    fmt_size = calcsize(fmt)
    
    mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

    # Generate list with required bytearrays for each frame and each object (assuming triangulated faces)
    frame_count = s.frame_end-s.frame_start+1 if self.frame_option == 'all' else 1
    arr = [{obj.name:bytearray(fmt_size*len(obj.data.polygons)*3) for obj in mesh_objects} for x in range(frame_count)]

    # List to contain binary vertex attribute data, before binary 'concat' (i.e. join)
    list = [0 for i in attribs]

    for i in range(frame_count):
        s.frame_set(s.frame_start+i)
        
        if 'scene' in map_unique:
            fetch_attribs(map_unique['scene'],s,list)
        
        # For each object in selection
        for obj in mesh_objects:
            # Generate a mesh with modifiers applied (not transforms!)
            data = obj.to_mesh(context.scene,True,'RENDER')
            
            # Apply object transform to mesh (TODO)
            # The above function doesn't do this...
            
            # Add object data
            if 'object' in map_unique:
                fetch_attribs(map_unique['object'],obj,list)
            
            uvs = data.uv_layers.active.data
            
            offset_index = 0   # Counter for offsets in bytearrays (TODO: per object)
            for p in data.polygons:
                if 'polygon' in map_unique:
                    fetch_attribs(map_unique['polygon'],p,list)
                
                if 'material' in map_unique:
                    mat = data.materials[p.material_index]
                    fetch_attribs(map_unique['material'],mat,list)
                    
                for li in p.loop_indices:
                    # First get loop index
                    loop = data.loops[li]
                    # Get vertex
                    v = data.vertices[loop.vertex_index]
                    
                    # Get UV
                    # TODO: get all uv's! (i.e. support multiple texture slots/stages)
                    uv = uvs[loop.index]
                    if 'uv' in map_unique:
                        fetch_attribs(map_unique['uv'],uv,list)
                    
                    # Get vertex attributes
                    if 'vertex' in map_unique:
                        fetch_attribs(map_unique['vertex'],v,list)
                    
                    # Now join attribute bytes together
                    # Remember: interpolated values aren't interpolated yet!
                    bytes = b''.join(list)
                    # Index 'calculations'
                    offset = offset_index * fmt_size
                    # Vertex format is always: block of current frame data, block of next frame data
                    # The below lines copy the current frame bytes to the current frame bytearray for the given object
                    # and copy the interpolated part of the current frame bytes to the previous frame bytearray for the given object
                    arr[i+0][obj.name][offset:offset+fmt_cur_size] = bytes[:fmt_cur_size]
                    arr[i-1][obj.name][offset+fmt_cur_size:offset+fmt_size] = bytes[fmt_cur_size:]
                    offset_index = offset_index + 1
        
    return arr

# Custom type to be used in collection
class AttributeType(bpy.types.PropertyGroup):
    type = bpy.props.StringProperty(name="Type", description="Where to get the data from", default="vertex")
    attr = bpy.props.StringProperty(name="Attribute", description="Which attribute to get", default="co")
    fmt = bpy.props.StringProperty(name="Format", description="The format string to be used for the binary data", default="fff")
    int = bpy.props.BoolProperty(name="Interpolated", description="Whether to write the interpolated value", default=False)
    func = bpy.props.StringProperty(name="Function", description="'Pre-processing' function to be called before conversion to binary format - must exist in globals()", default="")

# Operators to get the vertex format customization add/remove to work
# See https://blender.stackexchange.com/questions/57545/can-i-make-a-ui-button-that-makes-buttons-in-a-panel
class AddAttributeOperator(Operator):
    """Add a new attribute to the vertex format"""
    bl_idname = "export_scene.add_attribute_operator"
    bl_label = "Add Vertex Attribute"

    def execute(self, context):
        # context.active_operator refers to ExportGMSMultiTex instance
        context.active_operator.vertex_format.add()
        return {'FINISHED'}

class RemoveAttributeOperator(Operator):
    """Remove the selected attribute from the vertex format"""
    bl_idname = "export_scene.remove_attribute_operator"
    bl_label = "Remove Vertex Attribute"
    
    id = bpy.props.IntProperty()

    def execute(self, context):
        # context.active_operator refers to ExportGMSMultiTex instance
        context.active_operator.vertex_format.remove(self.id)
        return {'FINISHED'}

# Register these here already
bpy.utils.register_class(AttributeType)
bpy.utils.register_class(AddAttributeOperator)
bpy.utils.register_class(RemoveAttributeOperator)

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
class ExportGMSMultiTex(Operator, ExportHelper):
    """Export (part of) the current scene to a vertex buffer, including textures and a description file in JSON format"""
    bl_idname = "export_scene.gms_multitex" # important since its how bpy.ops.export_scene.gms_multitex is constructed
    bl_label = "Export GM:Studio Buffer MultiTexture"
    bl_options = {'PRESET'}                 # Allow presets of exporter configurations

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
    
    invert_uvs = BoolProperty(
        name="Invert UV's",
        description="Whether to invert UV's v (i.e. y) coordinate, i.e. (u,v) becomes (u,1-v)"
    )
    
    handedness = EnumProperty(
        name="Handedness",
        description="Handedness of the coordinate system to be used",
        items=(('r',"Right handed",""),
               ('l',"Left handed",""),
        )
    )
    
    vertex_format = CollectionProperty(
        name="Vertex Format",
        type=bpy.types.AttributeType,
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
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        
        box.label("General:")
        
        box.prop(self,'selection_only')
        box.prop(self,'frame_option')
        box.prop(self,'batch_mode')
        
        box = layout.box()
        
        box.label("Transforms:")
        
        box.prop(self,'invert_uvs')
        box.prop(self,'handedness')
        
        box = layout.box()
        
        box.label("Vertex Format:")
        
        box.operator("export_scene.add_attribute_operator",text="Add")
        
        for index, item in enumerate(self.vertex_format):
            row = box.row()
            row.prop(item,'type')
            row.prop(item,'attr')
            row.prop(item,'fmt')
            row.prop(item,'func')
            row.prop(item,'int')
            opt_remove = row.operator("export_scene.remove_attribute_operator",text="Remove")
            opt_remove.id = index
        
        box = layout.box()
        
        box.label("Extras:")
        
        box.prop(self,'vertex_groups')
        box.prop(self,'join_into_active')
        box.prop(self,'split_by_material')

    def execute(self, context):
        # TODO: preparation step
        
        
        # Join step
        if self.join_into_active:
            bpy.ops.object.join()
        
        # TODO: transformation and axes step
        
        
        # Split by material
        if self.split_by_material:
            bpy.ops.mesh.separate(type='MATERIAL')
        
        # First convert the contents of vertex_format to something we can use
        attribs = []
        #for i in self.attr:
        for i in self.vertex_format:
            if i.func == '':
                attribs.append((i.type,i.attr,{'fmt':i.fmt},'i' if i.int else ''))
            else:
                # Note: currently using globals() to get a globally defined function - might change in the future...
                # Important: a "bound method" is something different than a function and passes the 'self' as an additional parameter!
                attribs.append((i.type,i.attr,{'fmt':i.fmt,'func':globals()[i.func]},'i' if i.int else ''))
        
        # Now execute
        result = get_byte_data(self,attribs,context)
        
        # Final step: write to file(s)
        f = open(self.filepath,"wb")
        # TODO: per frame, per object, ...
        for frame in result:
            for obj in frame:
                f.write(frame[obj])
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