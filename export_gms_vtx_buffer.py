import bpy
import json
from struct import (
    pack,
    )


def triangulated_mesh_from_object(obj):
    """Important: use to_mesh_clear to free the mesh generated by this function"""
    mod_tri = obj.modifiers.new('triangulate_for_export','TRIANGULATE')
    mod_tri.quad_method = 'FIXED'   # FIX #20 Guarantee consistent triangulation between frames
    mod_tri.ngon_method = 'CLIP'    # This one too
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    m = obj_eval.to_mesh()
    obj.modifiers.remove(mod_tri)
    return m


def write_object_ba(scene,obj,desc,ba,frame,reverse_loop,apply_transforms):
    """Traverse the object's mesh data at the given frame and write to the
    appropriate bytearray in ba using the description data structure provided"""
    desc, vertex_format_bytesize = desc
    
    def fetch_attribs(desc,node,ba,byte_pos,frame,ctx=None):
        """"Fetch the attribute values from the given node and place in ba at byte_pos"""
        id = node.bl_rna.identifier
        if id in desc:
            for prop, occurences in desc[id].items():                         # Property name and occurrences in bytedata
                for offset, attr_blen, fmt, index, func, args in occurences:  # Each occurence's data (tuple assignment!)
                    ind = byte_pos+offset
                    val = getattr(node,prop)
                    if func != None:
                        if args == "":
                            val = func(val,ctx=ctx)
                        else:
                            val = func(val,ctx=ctx,args=json.loads(args))
                    val_bin = pack(fmt,val) if len(fmt) == 1 else pack(fmt,*val[:len(fmt)])
                    ba[frame-index][ind:ind+attr_blen] = val_bin
    
    m = triangulated_mesh_from_object(obj)
    if apply_transforms:
        # axis conversion probably needs to go here, too...
        m.transform(obj.matrix_world)
    
    # Setup context dict
    ctx = {}
    ctx['scene'] = scene
    ctx['object'] = obj
    
    ba_pos = 0
    for poly in m.polygons:
        ctx['polygon'] = poly
        iter = reversed(poly.loop_indices) if reverse_loop else poly.loop_indices
        for li in iter:
            fetch_attribs(desc,scene,ba,ba_pos,frame,ctx)
            fetch_attribs(desc,obj,ba,ba_pos,frame,ctx)
            
            fetch_attribs(desc,poly,ba,ba_pos,frame,ctx)
            
            if (len(m.materials) > 0):
                mat = m.materials[poly.material_index]
                fetch_attribs(desc,mat,ba,ba_pos,frame,ctx)
                
                """
                if mat.use_nodes:
                    # Get shader node that is directly attached to output node
                    output_nodes = [n for n in mat.node_tree.nodes if len(n.outputs) == 0]
                    if len(output_nodes) > 0:
                        output_node = output_nodes[0]   # Valid output node (only 1!)
                        attached_node = output_node.inputs[0].links[0].from_node
                else:
                    pass
                """
                """
                # Getting the shader values
                [input.default_value for input in node.inputs if input.type == 'VALUE']
                """
            
            loop = m.loops[li]
            ctx['loop'] = loop
            fetch_attribs(desc,loop,ba,ba_pos,frame,ctx)
            
            if (len(m.uv_layers) > 0):
                uvs = m.uv_layers.active.data
                uv = uvs[loop.index]                                # Use active uv layer
                fetch_attribs(desc,uv,ba,ba_pos,frame,ctx)
            
            vtx_colors = m.vertex_colors.active
            if vtx_colors:
                vtx_col = vtx_colors.data[li]                       # Vertex colors
                fetch_attribs(desc,vtx_col,ba,ba_pos,frame,ctx)
            
            vertex = m.vertices[loop.vertex_index]
            fetch_attribs(desc,vertex,ba,ba_pos,frame,ctx)
            
            # We wrote a full vertex, so we can now increment the bytearray position by the vertex format size
            ba_pos += vertex_format_bytesize
    
    obj.to_mesh_clear()


def construct_ds(obj,attr):
    """Constructs the data structure required to move through the attributes of a given object"""
    from struct import calcsize
    
    desc, offset = {}, 0
    for a in attr:
        ident, atn, format, fo, func, args = a
        
        if ident not in desc:
            desc[ident] = {}
        dct_obj = desc[ident]
        
        if atn not in dct_obj:
            dct_obj[atn] = []
        lst_attr = dct_obj[atn]
        
        prop_rna = getattr(bpy.types,ident).bl_rna.properties[atn]
        attrib_bytesize = calcsize(format)
        
        lst_attr.append((offset,attrib_bytesize,format,fo,func, args))
        offset += attrib_bytesize
        
    return (desc, offset)


def construct_ba(obj,desc,frame_count):
    """Construct the required bytearrays to store vertex data for the given object for the given number of frames"""
    m = triangulated_mesh_from_object(obj)
    no_verts = len(m.polygons) * 3
    obj.to_mesh_clear()                                   # Any easier way to get number of vertices??
    desc, vertex_format_bytesize = desc
    ba = [bytearray([0] * no_verts * vertex_format_bytesize) for i in range(0,frame_count)]
    return ba, no_verts


def object_to_json(obj):
    """Returns the data of the object in a json-compatible form"""
    result = {}
    rna = obj.bl_rna
    for prop in rna.properties:
        prop_id = prop.identifier
        prop_ins = getattr(obj,prop_id)
        prop_rna = rna.properties[prop_id]
        type = rna.properties[prop_id].type
        #print(prop_id,prop_ins,type)
        if type == 'STRING':
            result[prop_id] = prop_ins
        elif type == 'ENUM':
            result[prop_id] = [flag for flag in prop_ins] if prop_rna.is_enum_flag else prop_ins
        elif type == 'POINTER':
            result[prop_id] = getattr(prop_ins,'name','') if prop_ins != None else ''
        elif type == 'COLLECTION':
            # Enter collections up to encountering a PointerProperty
            result[prop_id] = [object_to_json(prop_item) for prop_item in prop_ins if prop_item != None]
            pass
        else:
            # 'Simple' attribute types: int, float, boolean
            if prop_rna.is_array:
                # Sometimes the bl_rna indicates a number of array items, but the actual number is less
                # That's because items are stored in an additional object, e.g. a matrix consists of 4 vectors
                len_expected, len_actual = prop_rna.array_length, len(prop_ins)
                if len_expected > len_actual:
                    result[prop_id] = []
                    for item in prop_ins: result[prop_id].extend(item[:])
                else:
                    result[prop_id] = prop_ins[:]
            else:
                result[prop_id] = prop_ins
    return result


def export(self, context):
    """Main entry point for export"""
    # TODO Get rid of context in this function
    
    from os.path import split, splitext
    
    # Prepare a bit
    root, ext = splitext(self.filepath)
    base, fname = split(self.filepath)
    fn = splitext(fname)[0]
    print("Root")
    print(root)
    scene = context.scene
    frame_count = scene.frame_end-scene.frame_start+1 if self.frame_option == 'all' else 1
    object_selection = context.selected_objects if self.selection_only else context.scene.objects
    mesh_selection = [obj for obj in object_selection if obj.type == 'MESH']
    for i, obj in enumerate(mesh_selection): obj.batch_index = i   # Guarantee a predictable batch index
    
    # FIX for issue #21
    no_verts_per_object = {}
    offset = {}
    for obj in mesh_selection:
        no_verts_per_object[obj] = 0
        offset[obj] = 0
    
    # Export mesh data to buffer
    if self.export_mesh_data:
        from . import conversions
        
        attribs = [(i.datapath[0].node,i.datapath[1].node,i.fmt,i.int,None if i.func == "none" else getattr(conversions,i.func),i.args) for i in self.vertex_format]
        #print(attribs)
        
        # << Prepare a structure to map vertex attributes to the actual contents >>
        ba_per_object = {}
        desc_per_object = {}
        for obj in mesh_selection:
            desc_per_object[obj] = construct_ds(obj,attribs)
            ba_per_object[obj], no_verts_per_object[obj] = construct_ba(obj,desc_per_object[obj],frame_count)
        
        # << End of preparation of structure >>
        
        # Loop through scene frames
        for i in range(frame_count):
            # First set the current frame
            scene.frame_set(scene.frame_start+i)
            
            # Now add frame vertex data for the current object
            for obj in mesh_selection:
                write_object_ba(scene,obj,desc_per_object[obj],ba_per_object[obj],i,self.reverse_loop,self.apply_transforms)
        
        # Final step: write all bytearrays to one or more file(s)
        # in one or more directories
        with open(root + ".vbx",self.file_mode) as f:
            offset = {}
            for obj in mesh_selection:
                ba = ba_per_object[obj]
                offset[obj] = f.tell()
                for b in ba:
                    f.write(b)
    
    # Create JSON description file
    if self.export_json_data:
        ctx, data = {}, {}
        json_data = {
            "bpy":{
                "context":ctx,
                "data":data
            }
        }
        
        # Export bpy.context
        ctx["selected_objects"] = [object_to_json(obj) for obj in object_selection]
        #ctx["scene"] = {"view_layers":{"layers":[{layer.name:[i for i in layer.layer_collection]} for layer in context.scene.view_layers]}}
        
        # Export bpy.data
        data_to_export = self.object_types_to_export
        for datatype in data_to_export:
            #data[datatype] = [object_to_json(obj) for obj in getattr(bpy.data,datatype)]
            data[datatype] = {obj.name:object_to_json(obj) for obj in getattr(bpy.data,datatype)}
        
        # Export additional info that might be useful
        json_data["blmod"] = {
            "mesh_data":{
                "location":fn + ".vbx",
                "format":[{"type":x.datapath[0].node,"attr":x.datapath[1].node,"fmt":x.fmt} for x in self.vertex_format],
                "ranges":{obj.name:{"no_verts":no_verts_per_object[obj],"offset":offset[obj]} for obj in mesh_selection},
            },
            "settings":{"apply_transforms":self.apply_transforms},
            "no_frames":frame_count,
            "blender_version":bpy.app.version[:],
            #"version":bl_info["version"],
        }
        
        import json
        f_desc = open(root + ".json","w")
        json.dump(json_data,f_desc)
        f_desc.close()
    
    # Save images (Cycles and Eevee materials)
    if self.export_images:
        materials = {slot.material for o in mesh_selection for slot in o.material_slots}
        node_based_materials = [mat for mat in materials if mat.use_nodes]
        for mat in node_based_materials:
            ntree = mat.node_tree
            
            """
            # More advanced traversal of tree
            output_node = [n for n in mat.node_tree.nodes if len(n.outputs) == 0]
            
            node = output_node
            while node:
                node = node.inputs[0].links[0].from_node    # Phew...
            """
            
            if len(ntree.nodes) > 1:    # Quite a couple of happy assumptions we make here...
                tex_node = [n for n in ntree.nodes if n.type == 'TEX_IMAGE']
                if len(tex_node) > 0:
                    tex_node = tex_node[0]
                    image = tex_node.image
                    if image:
                        image.save_render(base + '/' + image.name,scene=context.scene)
    
    # Cleanup: remove dynamic property from class
    del bpy.types.Object.batch_index
    
    return {'FINISHED'}