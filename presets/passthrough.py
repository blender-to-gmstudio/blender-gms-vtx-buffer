import bpy
op = bpy.context.active_operator

op.filepath = 'C:\\Users\\Dev\\Desktop\\data.json'
op.selection_only = True
op.vertex_format.clear()
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
item_sub_1.func = 'none'
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.datapath.clear()
item_sub_2 = item_sub_1.datapath.add()
item_sub_2.name = ''
item_sub_2.node = 'Material'
item_sub_2 = item_sub_1.datapath.add()
item_sub_2.name = ''
item_sub_2.node = 'diffuse_color'
item_sub_1.fmt = 'BBBB'
item_sub_1.int = 0
item_sub_1.func = 'vec_to_bytes'
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
item_sub_1.func = 'none'
op.reverse_loop = False
op.frame_option = 'cur'
op.batch_mode = 'one'
op.handedness = 'rh'
op.export_mesh_data = True
op.export_json_data = False
op.object_types_to_export = set()
op.export_json_filter = False
op.apply_transforms = True
op.join_into_active = False
op.split_by_material = False
op.export_textures = False
