import bpy
import json
from struct import (
    pack,
    )

# Mesh-like objects (the ones that can be converted to mesh)
MESHLIKE_TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}

def triangulated_mesh_from_object(obj):
    """Important: use to_mesh_clear to free the mesh generated by this function"""
    mod_tri = obj.modifiers.new('triangulate_for_export', 'TRIANGULATE')
    mod_tri.quad_method = 'FIXED'   # FIX #20 Guarantee consistent triangulation between frames
    mod_tri.ngon_method = 'CLIP'    # This one too
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    m = obj_eval.to_mesh()
    m.calc_normals_split()
    obj.modifiers.remove(mod_tri)
    return m


def write_object_ba(scene, obj, desc, ba, frame, reverse_loop, apply_transforms):
    """Traverse the object's mesh data at the given frame and write to the
    appropriate bytearray in ba using the description data structure provided"""
    desc, vertex_format_bytesize = desc

    def fetch_attribs(desc, node, ba, byte_pos, frame, ctx=None):
        """"Fetch the attribute values from the given node and place in ba at byte_pos"""
        id = node.bl_rna.identifier
        if id in desc:
            for prop, occurrences in desc[id].items():                          # Property name and occurrences in bytedata
                for offset, attr_blen, fmt, index, func, args in occurrences:   # Each occurrence's data (tuple assignment!)
                    ind = byte_pos + offset
                    if id.startswith('ShaderNode'):
                        # Write the input's default value for shader nodes
                        # TODO Trace back to value if a node is attached (if doable)
                        val = node.inputs[prop].default_value
                    else:
                        # Simply lookup the property on the node
                        val = getattr(node, prop)
                    
                    # Pass through pre-process function
                    if func != None:
                        if args == "":
                            val = func(val, ctx=ctx)
                        else:
                            val = func(val, ctx=ctx, args=json.loads(args))
                    
                    # Pack as bytes according to the chosen data type
                    # and write to correct position in the right bytearray
                    val_bin = pack(fmt, val) if len(fmt) == 1 else pack(fmt, *val[:len(fmt)])
                    ba[frame-index][ind:ind+attr_blen] = val_bin

    m = triangulated_mesh_from_object(obj)
    if apply_transforms:
        # axis conversion probably needs to go here, too...
        m.transform(obj.matrix_world)

    # Setup context dict
    ctx = {}
    ctx['scene'] = scene
    ctx['object'] = obj

    # Traverse the Blender data, starting at the polygons
    ba_pos = 0
    for poly in m.polygons:
        ctx['polygon'] = poly
        iter = reversed(poly.loop_indices) if reverse_loop else poly.loop_indices
        for li in iter:
            fetch_attribs(desc, scene, ba, ba_pos, frame, ctx)
            fetch_attribs(desc, obj, ba, ba_pos, frame, ctx)

            fetch_attribs(desc, poly, ba, ba_pos, frame, ctx)

            if m.materials:
                mat = m.materials[poly.material_index]
                fetch_attribs(desc, mat, ba, ba_pos, frame, ctx)

                if mat.use_nodes:
                    # Simply loop through all of this material's nodes
                    # (TODO could be optimized quite a bit..)
                    for node in mat.node_tree.nodes:
                        fetch_attribs(desc, node, ba, ba_pos, frame, ctx)
                

            loop = m.loops[li]
            ctx['loop'] = loop
            fetch_attribs(desc, loop, ba, ba_pos, frame, ctx)

            if m.uv_layers:
                uvs = m.uv_layers.active.data
                uv = uvs[loop.index]                                # Use active uv layer
                fetch_attribs(desc, uv, ba, ba_pos, frame, ctx)

            vtx_colors = m.vertex_colors.active
            if vtx_colors:
                vtx_col = vtx_colors.data[li]                       # Vertex colors
                fetch_attribs(desc, vtx_col, ba, ba_pos, frame, ctx)

            vertex = m.vertices[loop.vertex_index]
            fetch_attribs(desc, vertex, ba, ba_pos, frame, ctx)

            # We wrote a full vertex, so we can now increment the bytearray position by the vertex format size
            ba_pos += vertex_format_bytesize

    obj.to_mesh_clear()


def construct_ds(obj, attr):
    """ Constructs the data structure required to move through the attributes of a given object

    """
    from struct import calcsize

    description, offset = {}, 0
    for a in attr:
        ident, atn, format, fo, func, args = a

        if ident not in description:
            description[ident] = {}
        dct_obj = description[ident]

        if atn not in dct_obj:
            dct_obj[atn] = []
        lst_attr = dct_obj[atn]

        attrib_bytesize = calcsize(format)

        lst_attr.append((offset, attrib_bytesize, format, fo, func, args))
        offset += attrib_bytesize

    return (description, offset)


def construct_ba(obj, desc, frame_range):
    """Construct the required bytearrays to store vertex data
       for the given object for the given number of frames"""
    m = triangulated_mesh_from_object(obj)
    no_verts = len(m.polygons) * 3
    obj.to_mesh_clear()         # TODO Any easier way to get number of vertices??
    desc, vertex_format_bytesize = desc
    ba = [bytearray([0] * no_verts * vertex_format_bytesize) for f in frame_range]
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


def export(context, filepath,
        file_mode,
        selection_only,
        vertex_format,
        reverse_loop,
        frame_option,
        batch_mode,
        export_mesh_data,
        export_json_data,
        object_types_to_export,
        apply_transforms,
        export_images,
        custom_extension
        ):
    """Main entry point for export"""

    # TODO Get rid of context in this function

    from os.path import split, splitext

    # Prepare a bit
    root, ext = splitext(filepath)
    base, fname = split(filepath)
    fn = splitext(fname)[0]
    scene = context.scene

    # Work out the frames to export
    # frame_offset is used to index the correct bytearray! (index 0 for frame_start)
    if frame_option == 'all':
        # Full scene frame range, take the step value into account
        frame_range = range(scene.frame_start, scene.frame_end+1, scene.frame_step)
        frame_offset = scene.frame_start
    else:
        # Only the current frame
        frame_range = range(scene.frame_current, scene.frame_current+1)
        frame_offset = scene.frame_current  # Offset to subtract in the data buffer

    # Which models to export
    object_selection = context.selected_objects if selection_only else context.scene.objects
    mesh_selection = [obj for obj in object_selection if obj.type in MESHLIKE_TYPES]    # TODO Does this break morphs?
    for i, obj in enumerate(mesh_selection): obj.batch_index = i   # Guarantee a predictable batch index

    # Support alternative extension for model files
    ext = custom_extension if custom_extension else ".vbx"

    # FIX for issue #21
    no_verts_per_object = {}
    offset = {}
    for obj in mesh_selection:
        no_verts_per_object[obj] = 0
        offset[obj] = 0

    # Export mesh data to buffer
    if export_mesh_data:
        from . import conversions

        attribs = [(
            attrib.datapath[0].node,    # Node on which to look up attribute
            attrib.datapath[1].node,    # attribute to look up on the node
            attrib.fmt,
            attrib.int,
            None if attrib.func == "none" else getattr(conversions, attrib.func),
            attrib.args,
        ) for attrib in vertex_format]

        # << Prepare a structure to map vertex attributes to the actual contents >>
        ba_per_object = {}
        desc_per_object = {}
        for obj in mesh_selection:
            desc_per_object[obj] = construct_ds(obj, attribs)
            ba_per_object[obj], no_verts_per_object[obj] = construct_ba(obj, desc_per_object[obj], frame_range)

        # << End of preparation of structure >>

        # Loop through scene frames
        frame_prev = scene.frame_current

        for frame in frame_range:
            # First set the current frame
            scene.frame_set(frame)

            # Now add frame vertex data for the current object
            for obj in mesh_selection:
                write_object_ba(
                    scene,
                    obj,
                    desc_per_object[obj],
                    ba_per_object[obj],
                    frame - frame_offset,
                    reverse_loop,
                    apply_transforms,
                )

        # Nicely reset the previous frame
        scene.frame_set(frame_prev)

        # Final step: write all bytearrays to one or more file(s)
        # in one or more directories
        with open(root + ext, file_mode) as f:
            offset = {}
            for obj in mesh_selection:
                ba = ba_per_object[obj]
                offset[obj] = f.tell()
                for b in ba:
                    f.write(b)

    # Create JSON description file
    if export_json_data:
        ctx, data = {}, {}
        json_data = {
            "bpy":{
                "context":ctx,
                "data":data
            }
        }

        # Export bpy.context
        ctx["selected_objects"] = [object_to_json(obj) for obj in object_selection]

        # Export bpy.data
        data_to_export = object_types_to_export
        for datatype in data_to_export:
            #data[datatype] = [object_to_json(obj) for obj in getattr(bpy.data,datatype)]
            data[datatype] = {obj.name:object_to_json(obj) for obj in getattr(bpy.data, datatype)}

        # Export additional info that might be useful
        json_data["blmod"] = {
            "mesh_data":{
                "location":fn + ext,
                "format":[{"type":x.datapath[0].node,"attr":x.datapath[1].node,"fmt":x.fmt} for x in vertex_format],
                "ranges":{obj.name:{"no_verts":no_verts_per_object[obj],"offset":offset[obj]} for obj in mesh_selection},
            },
            "settings":{"apply_transforms":apply_transforms},
            "no_frames":len(frame_range),
            "blender_version":bpy.app.version[:],
            #"version":bl_info["version"],
        }

        import json
        with open(root + ".json", "w") as f_desc:
            json.dump(json_data, f_desc)

    # Save images (Cycles and Eevee materials)
    if export_images:
        materials = {slot.material for o in mesh_selection for slot in o.material_slots}
        node_based_materials = [mat for mat in materials if mat.use_nodes]
        for mat in node_based_materials:
            ntree = mat.node_tree

            if len(ntree.nodes) > 1:    # Quite a couple of happy assumptions we make here...
                tex_node = [n for n in ntree.nodes if n.type == 'TEX_IMAGE']
                if tex_node:
                    tex_node = tex_node[0]
                    image = tex_node.image
                    if image:
                        image.save_render(base + '/' + image.name, scene=context.scene)

    # Cleanup: remove dynamic property from class
    del bpy.types.Object.batch_index

    return {'FINISHED'}
