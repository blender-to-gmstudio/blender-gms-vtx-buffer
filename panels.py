import bpy
from struct import calcsize
from .export_gms_vtx_buffer import BUFFER_TYPE


def export_panel_general(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_general")
    
    header.use_property_split = False
    header.label(text="General", icon='SETTINGS')
    
    if body:
        box = body.box()

        if is_file_browser:
            box.prop(operator, property='selection_only')
        
        box.prop(operator, property='frame_option')
        box.prop(operator, property='file_mode')
        box.prop(operator, property='custom_extension')


def export_panel_attributes(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_attributes", default_closed=False)

    header.use_property_split = False
    header.prop(operator, "export_mesh_data", text="")
    header.label(text="Mesh Data", icon='MESH_DATA')

    if body:
        # See: properties_data_mesh.py (built-in Blender panel)
        contents = layout.box()
        
        box_header = contents.box()
        box_header.label(text="Vertex Data")
        
        box = contents.box()
        row = box.row()
        row.template_list("VBX_UL_vertex_format", "", operator, "vertex_format", operator, "active_attribute_index", sort_lock=True)
        col = row.column(align=True)
        col.operator("export_scene.add_attribute_operator", text="", icon='ADD')
        col.operator("export_scene.remove_attribute_operator", text="", icon='REMOVE')
        col.separator()
        col.operator("export_scene.move_up_attribute_operator", text="", icon='TRIA_UP')
        col.operator("export_scene.move_down_attribute_operator", text="", icon='TRIA_DOWN')
        
        info_box = contents.box()
        format_string = "".join([item.fmt for item in operator.vertex_format])
        info_box.label(text="Vertex format size: {0} bytes".format(calcsize(format_string)))


def export_panel_transforms(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_transforms")
    
    header.use_property_split = False
    header.label(text="Transforms", icon='CONSTRAINT')

    if body:
        box = body.box()
        box.prop(operator, property="apply_transforms")
        box.prop(operator, property="reverse_loop")


def export_panel_object_data(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_object_data", default_closed=True)

    header.use_property_split = False
    header.prop(operator, "export_json_data", text="")
    header.label(text="Object Data", icon='OBJECT_DATA')
    
    if body:
        box = body.box()
        box.prop(operator, property="object_types_to_export")


def export_panel_extra(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_extra", default_closed=True)

    header.use_property_split = False
    header.label(text="Extra", icon='PLUS')
    
    if body:
        box = body.box()
        box.prop(operator, property='export_images')
