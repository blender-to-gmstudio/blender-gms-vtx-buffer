# Export to GameMaker's passthrough vertex format
# as described in the manual under "Guide To Primitives And Vertex Building": 
# 
# https://manual.yoyogames.com/Additional_Information/Guide_To_Primitives_And_Vertex_Building.htm
#
# with an additional normal attribute added in the second position
# (i.e. the default passthrough shader with the in_Normal uncommented).
# 
# Positions and normals are written with y inverted,
# such that the top-down view in Blender corresponds
# to the top-down view in GameMaker's Room Editor
# (with a correct projection set up!)
# 
# The vertex color written is the mesh loop's color
# (MeshLoopColor.color)
# 

import bpy
op = bpy.context.active_operator

op.filepath = 'C:\\Users\\bart_\\Desktop\\cube'
op.file_mode = 'wb'
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
item_sub_1.func = 'invert_y'
item_sub_1.args = ''
item_sub_1 = op.vertex_format.add()
item_sub_1.name = ''
item_sub_1.datapath.clear()
item_sub_2 = item_sub_1.datapath.add()
item_sub_2.name = ''
item_sub_2.node = 'MeshLoop'
item_sub_2 = item_sub_1.datapath.add()
item_sub_2.name = ''
item_sub_2.node = 'normal'
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
op.reverse_loop = False
op.frame_option = 'cur'
op.batch_mode = 'one'
op.export_mesh_data = True
op.export_json_data = False
op.object_types_to_export = set()
op.apply_transforms = False
op.export_images = False
op.custom_extension = ''
