import bpy
op = bpy.context.active_operator

op.filepath = 'C:\\Users\\Dev\\Desktop\\animation.vbx'
op.selection_only = True
op.frame_option = 'cur'
op.batch_mode = 'one'
op.invert_uvs = False
op.handedness = 'r'
op.vertex_format.clear()
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.int = False
item_sub_1.attr = 'co'
item_sub_1.func = ''
item_sub_1.type = 'vertex'
item_sub_1.fmt = 'fff'
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.int = False
item_sub_1.attr = 'normal'
item_sub_1.func = ''
item_sub_1.type = 'vertex'
item_sub_1.fmt = 'fff'
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.int = False
item_sub_1.attr = 'index'
item_sub_1.func = ''
item_sub_1.type = 'object'
item_sub_1.fmt = 'f'
op.vertex_groups = False
op.join_into_active = False
op.split_by_material = False
