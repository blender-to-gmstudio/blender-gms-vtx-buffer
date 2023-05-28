import bpy

"""
class VBX_PT_export_header(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Header"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "export_header", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()
        box.operator("export_scene.add_header_operator", text="Add")

        for index, item in enumerate(operator.header_format):
            row = box.row()
            row.prop(item, property='value')
            row.prop(item, property='fmt')
            row.prop(item, property='func')
            row.prop(item, property='args')
            opt_remove = row.operator("export_scene.remove_header_operator", text="Remove")
            opt_remove.id = index
"""

class VBX_PT_export_attributes(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Mesh Data"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "export_mesh_data", text="")
        self.layout.label(text="", icon='MESH_DATA')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()
        box.operator("export_scene.add_attribute_operator", text="Add")

        for index, item in enumerate(operator.vertex_format):
            row = box.row()
            for node in item.datapath:
                row.prop(node, property='node')
            row.prop(item, property='fmt')
            row.prop(item, property='func')
            row.prop(item, property='int')
            row.prop(item, property='args')
            opt_remove = row.operator("export_scene.remove_attribute_operator", text="Remove")
            opt_remove.id = index

"""
class VBX_PT_export_footer(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Footer"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "export_footer", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()
        box.operator("export_scene.add_footer_operator", text="Add")

        for index, item in enumerate(operator.footer_format):
            row = box.row()
            row.prop(item, property='value')
            row.prop(item, property='fmt')
            row.prop(item, property='func')
            row.prop(item, property='args')
            opt_remove = row.operator("export_scene.remove_footer_operator", text="Remove")
            opt_remove.id = index
"""

class VBX_PT_general(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "General"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()
        #box.label(text="General:", icon='SETTINGS')

        box.prop(operator, property='selection_only')
        box.prop(operator, property='frame_option')
        box.prop(operator, property='file_mode')
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='SETTINGS')


class VBX_PT_extra(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Extra"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 20

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()

        box.prop(operator, property='export_images')
        box.prop(operator, property='custom_extension')
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUS')


class VBX_PT_transforms(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transforms"
    bl_parent_id = "FILE_PT_operator"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()

        #row = box.row()
        #row.prop(self,property='axis_forward')
        #row.prop(self,property='axis_up')

        box.prop(operator, property="apply_transforms")
        box.prop(operator, property="reverse_loop")
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='CONSTRAINT')


class VBX_PT_export_object_data(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Object Data"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 15

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_gms_vtx_buffer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        box = layout.box()

        box.prop(operator, property="object_types_to_export")
    
    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        layout = self.layout

        layout.prop(operator, "export_json_data", text="")
        layout.label(text="", icon='OBJECT_DATA')
