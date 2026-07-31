bl_info = {
    "name": "Export GameMaker Vertex Buffer",
    "description": "Exporter for GameMaker with highly customizable vertex format",
    "author": "Bart Teunis",
    "version": (1, 0, 14),
    "blender": (4, 5, 12),
    "location": "File > Export",
    "warning": "", # used for warning icon and text in addons panel
    "doc_url": "https://github.com/blender-to-gmstudio/blender-gms-vbx/wiki",
    "tracker_url": "https://github.com/blender-to-gmstudio/blender-gms-vtx-buffer/issues",
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "export_gms_vtx_buffer" in locals():
        importlib.reload(export_gms_vtx_buffer)
    if "conversions" in locals():
        importlib.reload(conversions)

import bpy
import sys
import os
import shutil
from . import conversions
from .panels import *
from .shaders import (
    get_shader_nodes_inputs,
    get_shader_input_attr
)
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    )
from bpy.types import AddonPreferences
from bpy_extras.io_utils import (
    ExportHelper,
    orientation_helper,
    )
from inspect import (
    getmembers,
    isfunction,
    )


class VBXAddonPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text = "Install default export presets that come with the add-on.")
        layout.label(text = "WARNING: existing presets with the same name will be overwritten!")
        layout.operator("export_scene.install_vbx_presets", text="Install Presets")


# Whether the vertex format definition was initialized a first time or not
initialized = False

# Set of currently supported sources
supported_sources = {
    'MeshVertex',
    'MeshLoop',
    'MeshUVLoop',
    #'ShapeKeyPoint',
    #'VertexGroupElement',
    'Material',
    'MeshLoopColor',
    'MeshPolygon',
    'Scene',
    'Object',
    'ShaderNodeBsdfPrincipled',    # indirect via .inputs (keys obtained via inputs.keys())
}
# Dictionary for storing shader node sources
supported_shader_node_sources = dict()

# Constant list containing all possible values at all levels
# Start by adding all RNA-based properties
# Shader node's inputs are added in ExportHelper.invoke
items_glob = []
for src in supported_sources:
    rna = getattr(bpy.types, src).bl_rna
    props = rna.properties
    items_glob.append((rna.identifier, rna.name, rna.description))
    items_glob.extend([(p.identifier, p.name, p.description) for p in props
        if p.type not in ['POINTER', 'STRING', 'ENUM', 'COLLECTION']])


class VertexAttributeType(bpy.types.PropertyGroup):
    def conversion_list(self, context):
        """ Get the list of conversion functions """
        item_list = []
        item_list.append(("none", "None", "Don't convert the value"))
        item_list.extend([(o[0], o[1].__name__, o[1].__doc__) for o in getmembers(conversions, isfunction)])
        return item_list

    def properties_callback(self, context):
        source = self.data_source
        if source.startswith('ShaderNode'):
            # This item is for a shader node
            global supported_shader_node_sources
            items = []
            items.extend(supported_shader_node_sources[source])
        else:
            # This item is for regular (Blender RNA) node
            props = getattr(bpy.types, self.data_source).bl_rna.properties
            items = [(p.identifier, p.name, p.description) for p in props
                    if p.type not in ['POINTER', 'STRING', 'ENUM', 'COLLECTION']]
        return items

    def sources_callback(self, context):
        global supported_sources
        items = []
        for src in supported_sources:
            rna = getattr(bpy.types, src).bl_rna
            items.append((rna.identifier, rna.name, rna.description))
        
        return items

    def set_format_from_type(self, context):
        type = self.data_source
        attr = self.data_property
        op = context.active_operator
        attribute = op.vertex_format[op.active_attribute_index]
        if type.startswith('ShaderNode'):
            map_fmt = {'VALUE': 'f', 'INT': 'i', 'BOOLEAN': '?', 'VECTOR': 'fff', 'RGBA': 'BBBB'}   # Add shader node input types
            datatype = get_shader_input_attr(type, attr, 'type')# Mapping for shader inputs
            attribute.fmt = map_fmt[datatype]
        else:
            att = getattr(bpy.types, type).bl_rna.properties[attr]
            map_fmt = {'FLOAT':'f','INT':'i', 'BOOLEAN':'?'}    # Mapping for RNA-based attributes
            datatype = map_fmt.get(att.type, '*')               # Asterisk '*' means "I don't know what this should be..."
            attribute.fmt = datatype * att.array_length if att.is_array else datatype

    # Actual properties
    data_source: bpy.props.EnumProperty(name="Source",description="Data Source",items=sources_callback,update=set_format_from_type)
    data_property: bpy.props.EnumProperty(name="Property",description="Property",items=properties_callback,update=set_format_from_type)
    fmt : bpy.props.StringProperty(name="Format", description="The format string to be used for the binary data", default="fff")
    int : bpy.props.IntProperty(name="Lerp", description="Interpolation offset, i.e. 0 means write value at current frame, 1 means write value at next frame", default=0, min=0, max=1)
    func : bpy.props.EnumProperty(name="Function", description="The 'pre-processing' function to be called before conversion to binary format", items=conversion_list, update=None)
    args : bpy.props.StringProperty(name="Params", description="A string representation in JSON of a dictionary with custom arguments to be passed to the 'pre-processing' function", default="")

# @orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportGMSVertexBuffer(bpy.types.Operator, ExportHelper):
    """Export (a selection of) the current scene to a vertex buffer, including textures and a description file in JSON format"""

    bl_idname = "export_scene.gms_vtx_buffer"
    bl_label = "Export GameMaker Vertex Buffer"
    bl_options = {'PRESET'}   # Allow presets of exporter configurations

    filename_ext = ""

    filter_glob : StringProperty(
        default="*.vbx;*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    file_mode: EnumProperty(
        name="File Mode",
        description="How to handle writing to files",
        items=(('wb',"Overwrite", "Overwrite existing data"),
               ('ab',"Append", "Append to existing"),
        )
    )

    selection_only : BoolProperty(
        name="Selection Only",
        default=True,
        description="Only export objects that are currently selected",
    )

    vertex_format : CollectionProperty(
        name="Vertex Format",
        type=VertexAttributeType,
    )

    reverse_loop : BoolProperty(
        name="Reverse Loop",
        default=False,
        description="Reverse looping through triangle indices",
    )

    frame_option : EnumProperty(
        name="Frame",
        description="Which frames to export",
        items=(('cur',"Current","Export current frame only"),
               ('all',"All","Export all frames in range"),
        )
    )

    batch_mode : EnumProperty(
        name="Batch Mode",
        description="How to split individual object data over files",
        items=(('one',"Single File", "Batch all into a single file"),
               ('perobj',"Per Object", "Create a file for each object in the selection"),
               ('perfra',"Per Frame", "Create a file for each frame"),
               ('objfra',"Per Object Then Frame", "Create a directory for each object with a file for each frame"),
               ('fraobj',"Per Frame Then Object", "Create a directory for each frame with a file for each object"),
        )
    )

    export_mesh_data : BoolProperty(
        name="Export Mesh Data",
        default=True,
        description="Whether to export mesh data to a separate, binary file (.vbx)",
    )

    export_json_data : BoolProperty(
        name="Export Object Data",
        default = False,
        description="Whether to export Blender data (bpy.data) in JSON format (WARNING: very limited)",
    )

    object_types_to_export : EnumProperty(
        name="Object Types",
        description="Which types of object data to export",
        options = {'ENUM_FLAG'},
        items=(('cameras',"Cameras","Export cameras"),
               ('lights',"Lights","Export lights"),
               ('speakers',"Speakers","Export speakers"),
               ('armatures',"Armatures","Export armatures"),
               ('materials',"Materials","Export materials"),
               ('textures',"Textures","Export textures"),
               ('actions',"Actions","Export actions"),
               ('curves',"Curves","Export curves"),
               ('collections',"Collections","Export collections"),
        )
    )

    apply_transforms : BoolProperty(
        name="Apply Transforms",
        default=True,
        description="Whether to apply object transforms to mesh data",
    )

    export_images : BoolProperty(
        name="Export Images",
        default=False,
        description="Export texture images to same directory as result file",
    )

    collection: StringProperty(
        name="Source Collection",
        description="Export only objects from this collection (and its children)",
        default="",
    )
    
    active_attribute_index: IntProperty(name="Active Attribute Index")

    def update_filter(self, context):
        """Update the file filter"""
        params = context.space_data.params
        custom_ext = self.custom_extension
        ext = ".vbx" if not custom_ext else custom_ext
        params.filter_glob = "*" + ext + ";*.json"
        bpy.ops.file.refresh()

    custom_extension: StringProperty(
        name="Ext",
        description="Custom file extension to use for model files, including the dot (leave blank for default (.vbx))",
        default="",
        update=update_filter    # See Blender issue 104221
    )
    
    """
    def init_passthrough(self):
        """"Initialize the export properties for a passthrough export""""
        op = self

        # op.vertex_format.clear()
        item_sub_1 = op.vertex_format.add()
        item_sub_1.name = ''
        item_sub_1.datapath.clear()
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'MeshVertex'
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'co'
        item_sub_1.fmt = 'fff'
        item_sub_1.int = 0
        item_sub_1.func = 'invert_y'
        item_sub_1.args = ''
        item_sub_1 = op.vertex_format.add()
        item_sub_1.name = ''
        item_sub_1.datapath.clear()
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'MeshLoopColor'
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'color'
        item_sub_1.fmt = 'BBBB'
        item_sub_1.int = 0
        item_sub_1.func = 'vec_to_bytes'
        item_sub_1.args = ''
        item_sub_1 = op.vertex_format.add()
        item_sub_1.name = ''
        item_sub_1.datapath.clear()
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'MeshUVLoop'
        item_sub_2 = item_sub_1.datapath.add()
        item_sub_2.name = ''
        item_sub_2.node = 'uv'
        item_sub_1.fmt = 'ff'
        item_sub_1.int = 0
        item_sub_1.func = 'invert_v'
        item_sub_1.args = ''
    """

    def invoke(self, context, event):
        # Blender Python trickery: dynamic addition of an index variable to the class
        bpy.types.Object.batch_index = bpy.props.IntProperty(name="Batch Index")    # Each instance now has a batch index!

        # Update items list, do this here as we have proper access to bpy here
        # bpy isn't properly initialized yet in global scope and returns "_RestrictedData"
        global items_glob, supported_sources, supported_shader_node_sources
        supported_shader_node_sources = get_shader_nodes_inputs()
        vals = supported_shader_node_sources.keys()
        #supported_sources.update(vals)
        #for src in vals:
        #    rna = getattr(bpy.types, src).bl_rna
        #    items_glob.append((rna.identifier, rna.name, rna.description))
        #    items_glob.extend([r for r in supported_shader_node_sources[src]])

        # Do some custom initialization, not using any preset file.
        global initialized
        if not initialized:
            #ExportGMSVertexBuffer.init_passthrough(self)
            pass

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        is_file_browser = context.space_data.type == 'FILE_BROWSER'
        
        export_panel_general(layout, self, is_file_browser)
        export_panel_attributes(layout, self, is_file_browser)
        export_panel_transforms(layout, self, is_file_browser)
        export_panel_object_data(layout, self, is_file_browser)
        export_panel_extra(layout, self, is_file_browser)

    def cancel(self, context):
        # Cleanup: remove dynamic property from class
        del bpy.types.Object.batch_index

    def execute(self, context):
        # Putting this here seems to fix #22
        bpy.types.Object.batch_index = bpy.props.IntProperty(name="Batch Index")

        from . import export_gms_vtx_buffer
        keywords = self.as_keywords(ignore=("check_existing", "filter_glob", "active_attribute_index"))
        result = export_gms_vtx_buffer.export(context, **keywords)
        global initialized
        initialized = True
        return result


# Operators to get the vertex format customization add/remove to work
# See https://blender.stackexchange.com/questions/57545/can-i-make-a-ui-button-that-makes-buttons-in-a-panel
class AddVertexAttributeOperator(bpy.types.Operator):
    """Add a new item to the vertex format"""
    bl_idname = "export_scene.add_attribute_operator"
    bl_label = "Add Vertex Attribute"

    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        op = context.active_operator
        
        item = op.vertex_format.add()
        op.active_attribute_index = len(op.vertex_format)-1
        
        item.data_source = 'MeshVertex'
        return {'FINISHED'}

class RemoveVertexAttributeOperator(bpy.types.Operator):
    """Remove the selected attribute from the vertex format"""
    bl_idname = "export_scene.remove_attribute_operator"
    bl_label = "Remove Vertex Attribute"

    id: bpy.props.IntProperty()

    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        op = context.active_operator
        op.vertex_format.remove(op.active_attribute_index)
        if op.active_attribute_index == len(op.vertex_format):
            op.active_attribute_index -= 1
        return {'FINISHED'}

class MoveUpVertexAttributeOperator(bpy.types.Operator):
    """Move up the selected attribute from the vertex format"""
    bl_idname = "export_scene.move_up_attribute_operator"
    bl_label = "Move Vertex Attribute Up"

    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        op = context.active_operator
        
        if op.active_attribute_index > 0:
            # See: https://blender.stackexchange.com/a/23637
            op.vertex_format.move(op.active_attribute_index, op.active_attribute_index-1)
            op.active_attribute_index -= 1
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class MoveDownVertexAttributeOperator(bpy.types.Operator):
    """Move down the selected attribute from the vertex format"""
    bl_idname = "export_scene.move_down_attribute_operator"
    bl_label = "Move Vertex Attribute Down"

    def execute(self, context):
        # context.active_operator refers to ExportGMSVertexBuffer instance
        op = context.active_operator
        
        if op.active_attribute_index < len(op.vertex_format) - 1:
            # See: https://blender.stackexchange.com/a/23637
            op.vertex_format.move(op.active_attribute_index, op.active_attribute_index+1)
            op.active_attribute_index += 1
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class InstallVBXPresetsOperator(bpy.types.Operator):
    """Install presets in (user) presets directory"""
    bl_idname = "export_scene.install_vbx_presets"
    bl_label = "Install Export Presets"

    def execute(self, context):
        addon_dir = os.path.dirname(__file__)
        presets_dir = addon_dir + os.sep + "presets"
        dir2 = os.path.abspath(addon_dir + os.sep + ".." + os.sep + "..")
        new_presets_dir = os.sep.join([dir2, "presets", "operator", ExportGMSVertexBuffer.bl_idname])

        dest = shutil.copytree(presets_dir, new_presets_dir, dirs_exist_ok=True)

        self.report({'INFO'}, ("Export GameMaker Vertex Buffer\n"
                               "Export presets copied to: {0}").format(dest))

        return {'FINISHED'}


class IO_FH_vbx(bpy.types.FileHandler):
    bl_idname = "IO_FH_vbx"
    bl_label = "VBX (GameMaker Vertex Buffer)"
    bl_export_operator = ExportGMSVertexBuffer.bl_idname
    bl_file_extensions = ".vbx"


def menu_func_export(self, context):
    self.layout.operator(ExportGMSVertexBuffer.bl_idname, text="GameMaker Vertex Buffer (*.vbx + *.json)")


# See: https://docs.blender.org/api/current/bpy.types.UIList.html
# 
class VBX_UL_vertex_format(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row()
        
        group = row.row(align=True)
        
        group.label(text="Source")
        #for node in item.datapath:
        #    group.prop(node, property='node')
        group.prop(item, 'data_source', text="")
        group.prop(item, 'data_property', text="")
        
        row.separator(type='LINE')
        
        group = row.row(align=True)
        
        group.label(text="Output")
        group.prop(item, property='func', text="")
        group.prop(item, property='fmt', text="")
        group.prop(item, property='args', text="")
        
        row.separator(type='LINE')
        
        group = row.row(align=True)
        
        group.label(text="Frame")
        group.prop(item, property='int', text="")


classes = [
    VertexAttributeType,
    AddVertexAttributeOperator,
    RemoveVertexAttributeOperator,
    MoveUpVertexAttributeOperator,
    MoveDownVertexAttributeOperator,
    InstallVBXPresetsOperator,
    VBX_UL_vertex_format,
]

classes.append(VBXAddonPreferences)
classes.append(ExportGMSVertexBuffer)
classes.append(IO_FH_vbx)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
