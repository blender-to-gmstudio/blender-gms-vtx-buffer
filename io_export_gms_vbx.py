bl_info = {
    "name": "Export GM:Studio Vertex Buffer",
    "description": "Vertex buffer exporter for GM:Studio with customizable vertex format",
    "author": "Bart Teunis",
    "version": (0, 7, 0),
    "blender": (2, 78, 0),
    "location": "File > Export",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Import-Export"}

# Required imports
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Object, Operator, PropertyGroup
import bpy
import shutil                       # for image file copy
import json
from os import path, makedirs
from os.path import splitext, split
from struct import pack, calcsize

# Conversion functions (go into the globals() dictionary for now...)
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

# Currently supported attribute sources, maintained manually at the moment
supported_sources = {'MeshVertex','MeshLoop','MeshUVLoop','ShapeKeyPoint','VertexGroupElement','Material','MeshLoopColor','MeshPolygon','Scene','Object'}
source_items = []
for src in supported_sources:
    id = getattr(bpy.types,src)
    rna = id.bl_rna
    source_items.append((rna.identifier,rna.name,rna.description))

def test_cb(self,context):
    props = getattr(bpy.types,self.type).bl_rna.properties
    items = [(p.identifier,p.name,p.description) for p in props]
    
    return items

# Custom type to be used in collection
class AttributeType(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(name="Source", description="Where to get the data from", items=source_items)
    attr = bpy.props.EnumProperty(name="Attribute", description="Which attribute to get", items=test_cb)
    fmt = bpy.props.StringProperty(name="Format", description="The format string to be used for the binary data", default="fff")
    int = bpy.props.BoolProperty(name="Interpolated", description="Whether to write the interpolated value (value in next frame)", default=False)
    func = bpy.props.StringProperty(name="Function", description="'Pre-processing' function to be called before conversion to binary format - must exist in globals()", default="")

# Operators to get the vertex format customization add/remove to work
# See https://blender.stackexchange.com/questions/57545/can-i-make-a-ui-button-that-makes-buttons-in-a-panel
class AddAttributeOperator(Operator):
    """Add a new attribute to the vertex format"""
    bl_idname = "export_scene.add_attribute_operator"
    bl_label = "Add Vertex Attribute"

    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        context.active_operator.vertex_format.add()
        return {'FINISHED'}

class RemoveAttributeOperator(Operator):
    """Remove the selected attribute from the vertex format"""
    bl_idname = "export_scene.remove_attribute_operator"
    bl_label = "Remove Vertex Attribute"
    
    id = bpy.props.IntProperty()
    
    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        context.active_operator.vertex_format.remove(self.id)
        return {'FINISHED'}

# Register these here already
bpy.utils.register_class(AttributeType)
bpy.utils.register_class(AddAttributeOperator)
bpy.utils.register_class(RemoveAttributeOperator)

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
class ExportGMSVertexBuffer(Operator, ExportHelper):
    """Export (part of) the current scene to a vertex buffer, including textures and a description file in JSON format"""
    bl_idname = "export_scene.gms_vbx" # important since its how bpy.ops.export_scene.gms_vbx is constructed
    bl_label = "Export GM:Studio Vertex Buffer"
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
    
    reverse_loop = BoolProperty(
        name="Reverse Loop",
        default=False,
        description="Reverse looping through triangle indices",
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
    
    handedness = EnumProperty(
        name="Handedness",
        description="Handedness of the coordinate system to be used",
        items=(('rh',"Right handed",""),
               ('lh',"Left handed",""),
        )
    )
    
    vertex_format = CollectionProperty(
        name="Vertex Format",
        type=bpy.types.AttributeType,
    )
    
    preparation_step = BoolProperty(
        name="Preparation Step",
        default=False,
        description="Try to make duplicates real and link content from external .blend files"
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
    
    export_textures = BoolProperty(
        name="Export Textures",
        default=True,
        description="Export texture images to same directory as result file",
    )
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        
        box.label("General:")
        
        box.prop(self,'selection_only')
        box.prop(self,'frame_option')
        box.prop(self,'batch_mode')
        
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
        
        box.label("Transforms:")
        
        box.prop(self,'handedness')
        box.prop(self,'reverse_loop')
        
        box = layout.box()
        
        box.label("Extras:")
        
        box.prop(self,'preparation_step')
        box.prop(self,'join_into_active')
        box.prop(self,'split_by_material')
        box.prop(self,'export_textures')

    def execute(self, context):
        # Get all attributes from ref, defined in attr
        # and place them at appropriate indexes in list
        def fetch_attribs(attr,ref,list):
            for attrib in attr:
                fmt, indices = attr[attrib]['fmt'], attr[attrib]['pos']
                val = getattr(ref,attrib)
                if 'func' in attr[attrib]:
                    val = attr[attrib]['func'](val)
                val_bin = pack(fmt,val) if len(fmt) == 1 else pack(fmt,*val)
                for j in indices:
                    list[j] = val_bin
        
        # Prepare a bit
        root, ext = splitext(self.filepath)
        base, fname = split(self.filepath)
        
        # Preparation step
        if self.preparation_step:
            bpy.ops.object.duplicates_make_real()
            bpy.ops.object.make_local(type='SELECT_OBDATA') # TODO: also MATERIAL??
            bpy.ops.object.make_single_user(object=True,obdata=True,material=False,texture=False,animation=False)
            bpy.ops.object.convert(target='MESH')           # Applies modifiers, etc.
        
        # Join step
        if self.join_into_active:
            bpy.ops.object.join()
        
        # TODO: transformation and axes step
        
        
        # Split by material
        if self.split_by_material:
            bpy.ops.mesh.separate(type='MATERIAL')
        
        mesh_selection = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        # Blender Python trickery: dynamic addition of an index variable to the class
        bpy.types.Object.index = bpy.props.IntProperty()    # Each instance now has an index!
        for i, obj in enumerate(mesh_selection):
            obj.index = i
        
        # << Prepare a structure to map vertex attributes to the actual contents >>
        
        # First convert the contents of vertex_format to something we can use
        # TODO: support collections
        attribs = []
        for i in self.vertex_format:
            if i.func == '':
                attribs.append((i.type,i.attr,{'fmt':i.fmt},'i' if i.int else ''))
            else:
                # Note: currently using globals() to get a globally defined function - might (and should) change in the future...
                # Important: a "bound method" is something different than a function and passes the 'self' as an additional parameter!
                attribs.append((i.type,i.attr,{'fmt':i.fmt,'func':globals()[i.func]},'i' if i.int else ''))
        
        print(attribs)
        
        attribs2 = [{(i.type,i.attr):{'fmt':i.fmt,'func':globals()[i.func] if i.func != '' else '','int':i.int}} for i in self.vertex_format]
        print(attribs2)
        
        lerp_mask = [x.int for x in self.vertex_format]
        print(lerp_mask)
        
        # Convert linear list to nested dictionary for easier access while looping
        map_unique = {}
        
        for a in attribs:
            map_unique[a[0]] = dict()
        
        for a in attribs:
            map_unique[a[0]][a[1]]  = a[2]
            map_unique[a[0]][a[1]]['pos']  = []
        
        for i, a in enumerate(attribs):
            map_unique[a[0]][a[1]]['pos'].append(i)
        
        print(map_unique)
        
        #Get all indices in the attributes array that will contain interpolated values
        lerped_indices = [i for i,x in enumerate(attribs) if len(x) == 4 and x[3] == 'i']
        lerp_start = lerped_indices[0] if len(lerped_indices) > 0 else len(lerped_indices)  # Index of first interpolated attribute value

        # Get format strings and sizes
        fmt_cur = ''.join([a[2]['fmt'] for a in attribs[:lerp_start]])  # Current attribs format
        fmt     = ''.join([a[2]['fmt'] for a in attribs])               # All attribs format
        fmt_cur_size = calcsize(fmt_cur)
        fmt_size = calcsize(fmt)
        
        # << End of preparation of structure >>
        
        # << Now execute >>
        
        # Format of return value is: [{'obj1':bytearray,'obj2':bytearray},{'obj1':bytearray,'obj2':bytearray}]
        
        # Dictionary to store additional info per object
        object_info = {}
        
        # Get objects
        s = context.scene
        
        offset_index = {obj:0 for obj in mesh_selection}
        
        # Generate list with required bytearrays for each frame and each object (assuming triangulated faces)
        frame_count = s.frame_end-s.frame_start+1 if self.frame_option == 'all' else 1
        for obj in mesh_selection:
            mod_tri = obj.modifiers.new('to_triangles','TRIANGULATE')
            data = obj.to_mesh(context.scene,True,'RENDER')
            obj.modifiers.remove(mod_tri)
            object_info[obj] = len(data.polygons)*3     # Assuming triangulated faces
            bpy.data.meshes.remove(data)
        result = [{obj:bytearray(fmt_size*object_info[obj]) for obj in mesh_selection} for x in range(frame_count)]
        
        # List to contain binary vertex attribute data, before binary 'concat' (i.e. join)
        # Initialize each item with a null byte sequence of the appropriate length
        list = []
        for i in attribs:
            fmt = i[2]['fmt']
            list.append(pack(fmt,*([0]*len(fmt))))
        
        # Loop through scene frames
        for i in range(frame_count):
            s.frame_set(s.frame_start+i)
            
            if 'Scene' in map_unique:
                fetch_attribs(map_unique['Scene'],s,list)
            
            # For each object in selection
            for obj in mesh_selection:
                # Add a temporary triangulate modifier, to make sure we get triangles
                mod_tri = obj.modifiers.new('to_triangles','TRIANGULATE')
                data = obj.to_mesh(context.scene,True,'RENDER')
                obj.modifiers.remove(mod_tri)
                
                # Apply object transform to mesh => not going to happen, since join is meant for this
                
                # Add object data
                # TODO: obj.bl_rna.properties, bpy.types, ...
                if 'Object' in map_unique:
                    fetch_attribs(map_unique['Object'],obj,list)
                
                if 'MeshUVLoop' in map_unique:
                    uvs = data.uv_layers.active.data                # TODO: handle case where object/mesh has no uv maps
                
                if 'MeshLoopColor' in map_unique:
                    vertex_colors = data.vertex_colors.active.data  # TODO: handle case where object/mesh has no vertex colours
                
                offset_index[obj] = 0   # Counter for offsets in bytearrays
                for p in data.polygons:
                    if 'MeshPolygon' in map_unique:
                        fetch_attribs(map_unique['MeshPolygon'],p,list)
                    
                    mat = data.materials[p.material_index]
                    if 'Material' in map_unique:
                        fetch_attribs(map_unique['Material'],mat,list)
                    
                    if self.reverse_loop:
                        iter = reversed(p.loop_indices)
                    else:
                        iter = p.loop_indices
                    for li in iter:
                        loop = data.loops[li]
                        
                        # Get loop attributes
                        if 'MeshLoop' in map_unique:
                            fetch_attribs(map_unique['MeshLoop'],loop,list)
                        
                        # Get vertex
                        v = data.vertices[loop.vertex_index]
                        
                        # Get vertex group stuff
                        if 'VertexGroupElement' in map_unique:
                            g = v.groups[0]     # TESTING Single vertex group
                            fetch_attribs(map_unique['VertexGroupElement'],g,list)
                        
                        # Get UV
                        # TODO: get all uv's! (i.e. support multiple texture slots/stages)
                        if 'MeshUVLoop' in map_unique:
                            uv = None
                            for slot in [x for x in mat.texture_slots if x != None and x.texture_coords == 'UV']:
                                if slot.uv_layer == '':
                                    uv = uvs[loop.index]                                # Use default uv layer
                                else:
                                    uv = data.uv_layers[slot.uv_layer].data[loop.index] # Use the given uv layer
                            
                            if uv != None:
                                fetch_attribs(map_unique['MeshUVLoop'],uv,list)
                        
                        # Get vertex colour
                        if 'MeshLoopColor' in map_unique:
                            vtx_col = vertex_colors[loop.index]
                            fetch_attribs(map_unique['MeshLoopColor'],vtx_col,list)
                        
                        # Get shape key coordinates
                        if 'ShapeKeyPoint' in map_unique:
                            kbs = data.shape_keys.key_blocks
                            for kb in kbs:
                                fetch_attribs(map_unique['ShapeKeyPoint'],kb.data,list)
                        
                        # Get vertex attributes
                        if 'MeshVertex' in map_unique:
                            fetch_attribs(map_unique['MeshVertex'],v,list)
                        
                        # Now join attribute bytes together
                        # Remember: interpolated values aren't interpolated yet!
                        bytes = b''.join(list)
                        # Index 'calculations'
                        offset = offset_index[obj] * fmt_size
                        # Vertex format is always: block of current frame data, block of next frame data
                        # The below lines copy the current frame bytes to the current frame bytearray for the given object
                        # and copy the interpolated part of the current frame bytes to the previous frame bytearray for the given object
                        result[i-0][obj][offset:offset+fmt_cur_size] = bytes[:fmt_cur_size]
                        result[i-1][obj][offset+fmt_cur_size:offset+fmt_size] = bytes[fmt_cur_size:]
                        offset_index[obj] = offset_index[obj] + 1
                
                # Remove the mesh
                bpy.data.meshes.remove(data)
        
        # Final step: write all bytearrays to one or more file(s) in one or more directories
        offset = 0
        offset_per_obj = dict()
        f = open(self.filepath,"wb")
        # TODO: per frame, per object, ...
        for frame in result:
            # TODO: create new directory
            #if not path.exists(directory):
            #   makedirs(directory)
            
            for obj in frame:
                # TODO: create new file
                f.write(frame[obj])
                offset_per_obj[obj] = offset
                offset += len(frame[obj])
        f.close()
        
        # Create JSON file (very basic at the moment...)
        # Coming up next: 
        # for type_collection in [bpy.data.meshes,bpy.data.objects,bpy.data.materials,bpy.data.images,bpy.data.textures,bpy.data.cameras,bpy.data.lamps]:
        #    [{i:getattr(ins,i) for i in ins.bl_rna.properties.keys()} for ins in type_collection]
        
        # TODO: either add extra info as a header to the binary format or as external JSON file
        desc = {}
        desc["objects"]   = [{
                            "name":obj.name,
                            "type":obj.type,
                            "file":path.basename(self.filepath),
                            "offset":offset_per_obj[obj],
                            "no_verts":object_info[obj],
                            "index":obj.index,
                            "location":obj.location[:] if self.handedness == 'rh' else invert_y(obj.location)[:],
                            "rotation":obj.rotation_euler[:],
                            "scale":obj.scale[:],
                            "materials":[mat.name for mat in obj.material_slots],
                            "alpha": obj.material_slots[0].material.alpha,
                            "diffuse_color": obj.material_slots[0].material.diffuse_color[:],
                            "texture":obj.material_slots[0].material.texture_slots[0].texture.image.name if obj.material_slots[0].material.texture_slots[0] != None else "", # Yuck...
                            "vertex_groups":[vg.name for vg in obj.vertex_groups]
                            }
                            for obj in mesh_selection]
        cameras = [{
            "name":obj.name,
            "type":obj.type,
            "location":obj.location[:],
            "rotation":obj.rotation_euler[:],
            "scale":obj.scale[:],
            "angle":obj.data.angle,
            "clip_start":obj.data.clip_start,
            "clip_end":obj.data.clip_end,
            "cam_type":obj.data.type
        }
        for obj in context.selected_objects if obj.type == 'CAMERA']
        lamps = [{
            "name":obj.name,
            "type":obj.type,
            "location":obj.location[:],
            "rotation":obj.rotation_euler[:],
            "scale":obj.scale[:],
            "lamp_type":obj.data.type,
            "use_diffuse":obj.data.use_diffuse,
            "use_specular":obj.data.use_specular,
            "energy":obj.data.energy
        }
        for obj in context.selected_objects if obj.type == 'LAMP']
        speakers = [{
            "name":obj.name,
            "type":obj.type,
            "location":obj.location[:],
            "rotation":obj.rotation_euler[:],
            "scale":obj.scale[:],
            "volume":obj.data.volume,
            "pitch":obj.data.pitch,
            "volume_min":obj.data.volume_min,
            "volume_max":obj.data.volume_max,
            "attenuation":obj.data.attenuation,
            "distance_max":obj.data.distance_max,
            "distance_reference":obj.data.distance_reference
        }
        for obj in context.selected_objects if obj.type == 'SPEAKER']
        emptys = [{
            "name":obj.name,
            "type":obj.type,
            "location":obj.location[:],
            "rotation":obj.rotation_euler[:],
            "scale":obj.scale[:],
            "dupli_type":obj.dupli_type,
            "dupli_group":obj.dupli_group
        }
        for obj in context.selected_objects if obj.type == 'EMPTY']
        armatures = [{
            "name":obj.name,
            "type":obj.type,
            "location":obj.location[:],
            "rotation":obj.rotation_euler[:],
            "scale":obj.scale[:]
        }
        for obj in context.selected_objects if obj.type == 'ARMATURE']
        desc["objects"].extend(cameras)
        desc["objects"].extend(lamps)
        desc["objects"].extend(speakers)
        desc["objects"].extend(emptys)
        desc["objects"].extend(armatures)
        desc["format"]    = [{"type":x.type,"attr":x.attr,"fmt":x.fmt} for x in self.vertex_format]
        desc["no_frames"] = frame_count                             # Number of frames that are exported
        desc["materials"] = [mat.name for mat in bpy.data.materials]
        
        # Save textures
        if self.export_textures:
            for obj in mesh_selection:                              # Only mesh objects have texture slots
                tex_slot = obj.material_slots[0].material.texture_slots[0]
                if tex_slot != None:
                    image = tex_slot.texture.image
                    image.save_render(base + '/' + image.name,context.scene)
        
        f_desc = open(root + ".json","w")
        
        json.dump(desc,f_desc)
        
        f_desc.close()
        
        # Cleanup: remove dynamic property from class
        del bpy.types.Object.index
        
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportGMSVertexBuffer.bl_idname, text="GM:Studio Vertex Buffer (*.vbx)")


def register():
    bpy.utils.register_class(ExportGMSVertexBuffer)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportGMSVertexBuffer)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()