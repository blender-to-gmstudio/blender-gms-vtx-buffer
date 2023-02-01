# Export preset to a model file with .vbuff extension, for the GMC tutorial found at:
# 
# https://forum.gamemaker.io/index.php?threads/directional-light-and-shadows-in-3d.73264/
# 
# Make sure to add a vertex color in Blender by going into Vertex Paint mode.
# The model will export but vertex colors will be all black when exporting.
# 

import bpy
op = bpy.context.active_operator

op.filepath = 'C:\\Users\\bart_\\Documents\\GameMakerStudio2\\3D_Directional_Lighting_final.yyp\\datafiles\\suzanne'
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
item_sub_1.func = 'none'
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
item_sub_1.func = 'none'
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
op.apply_transforms = True
op.export_images = False
op.custom_extension = '.vbuff'
