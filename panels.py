import bpy
from struct import calcsize
from .export_gms_vtx_buffer import BUFFER_TYPE


def export_panel_general(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_general")
    
    header.use_property_split = False
    header.label(text="General", icon='SETTINGS')
    
    if body:
        box = body.box()

        box.prop(operator, property='selection_only')
        box.prop(operator, property='frame_option')
        box.prop(operator, property='file_mode')
        box.prop(operator, property='custom_extension')


def export_panel_attributes(layout, operator, is_file_browser):
    header, body = layout.panel("VBX_export_attributes")
    
    header.use_property_split = False
    header.prop(operator, "export_mesh_data", text="")
    header.label(text="Mesh Data", icon='MESH_DATA')
    
    if body:
        body.grid_flow(columns=0, even_columns=False, even_rows=False, align=True)
        body.alignment = 'LEFT'

        contents = body.box()
        header_box = contents.box()
        header_box.alignment = 'RIGHT'
        r = header_box.row()
        r.label(text="Vertex Data")
        r.operator("export_scene.add_attribute_operator", text="Add Item")

        format_box = contents.box()
        format_string = ""
        for index, item in enumerate(operator.vertex_format):
            box = format_box.box()
            row = box.row()
            group = row.row(align=True)
            group.label(text="Source")
            for node in item.datapath:
                group.prop(node, property='node')
            group = row.row(align=True)
            group.label(text="Output")
            group.prop(item, property='func', text="")
            group.prop(item, property='fmt', text="")
            format_string += item.fmt
            group.prop(item, property='args', text="")
            group = row.row(align=True)
            group.label(text="Frame")
            group.prop(item, property='int', text="")
            group = row.row(align=True)
            opt_remove = group.operator("export_scene.remove_attribute_operator", text="", icon='REMOVE')
            opt_remove.id = index
            #group.label(text=str(len(item.fmt)) + "x" + BUFFER_TYPE[item.fmt[0]])
            row.separator(factor=0)
        
        info_box = contents.box()
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
