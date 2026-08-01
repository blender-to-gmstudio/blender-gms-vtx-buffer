# Export to the default vertex format as defined
# in the DDD Editor (Penguin) software found at:
# 
# https://dragonite.itch.io/penguin
# 

import bpy
op = bpy.context.active_operator

#op.filepath = ''
op.file_mode = 'wb'
op.selection_only = True
op.vertex_format.clear()
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.data_source = 'MeshVertex'
item_sub_1.data_property = 'co'
item_sub_1.fmt = 'fff'
item_sub_1.int = 0
item_sub_1.func = 'none'
item_sub_1.args = ''
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.data_source = 'MeshPolygon'
item_sub_1.data_property = 'normal'
item_sub_1.fmt = 'fff'
item_sub_1.int = 0
item_sub_1.func = 'none'
item_sub_1.args = ''
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.data_source = 'MeshUVLoop'
item_sub_1.data_property = 'uv'
item_sub_1.fmt = 'ff'
item_sub_1.int = 0
item_sub_1.func = 'invert_v'
item_sub_1.args = ''
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.data_source = 'MeshLoopColor'
item_sub_1.data_property = 'color'
item_sub_1.fmt = 'BBBB'
item_sub_1.int = 0
item_sub_1.func = 'vec_to_bytes'
item_sub_1.args = ''
op.reverse_loop = False
op.frame_option = 'cur'
op.batch_mode = 'one'
op.export_mesh_data = True
op.export_json_data = False
op.object_types_to_export = set()
op.apply_transforms = True
op.export_images = False
op.custom_extension = '.vbuff'
