import bpy,os,json,shutil,mathutils,math,numpy,copy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from mathutils import Vector,Quaternion
from .KuroMDLTools import kuro_mdl_to_basic_gltf, kuro_mdl_import_meshes, kuro_mdl_export_meshes, kuro_gltf_to_meshes, lib_fmtibvb
from .io_scene_gltf2.blender.imp.blender_gltf import BlenderGlTF
from .io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
from .io_scene_gltf2.io.com.gltf2_io import Gltf, gltf_from_dict
from .io_scene_gltf2.blender.exp.export import __export as gltf2_blender_export
########################## Divider ##########################
#TODO:导入删除配置
########################## Divider ##########################
#https://sinestesia.co/blog/tutorials/using-uilists-in-blender/
class TextureItem(bpy.types.PropertyGroup):
    texture_image_name:bpy.props.StringProperty(
        description="",
        default="")
    texture_slot:bpy.props.IntProperty(
        description="",
        default=0)
    
class MaterialListItem(bpy.types.PropertyGroup):
    ref_name:bpy.props.StringProperty(
        description="",
        default="")
    enabled:bpy.props.BoolProperty(
        default=True,
        options={"HIDDEN"}
        )
    id_referenceonly:bpy.props.StringProperty(
        description="",
        default="-1")
    material_name:bpy.props.StringProperty(
        description="",
        default="")
    textures:bpy.props.CollectionProperty(type = TextureItem)
    value:bpy.props.StringProperty(
        description="",
        default="")

class MetadataListItem(bpy.types.PropertyGroup):
    enabled:bpy.props.BoolProperty(
        default=False,
        options={"HIDDEN"}
        )
    metadata_name:bpy.props.StringProperty(
        description="",
        default="")
    value:bpy.props.StringProperty(
        description="",
        default="{}")

class P_UL_Material_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=f"{item.ref_name.replace("_material_struct", "")}", icon = custom_icon)
            layout.label(text=f"{item.id_referenceonly}-{item.material_name}")
            layout.prop(item, "enabled", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

class P_UL_Metadata_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=f"{item.metadata_name.replace("_gltf_metadata", "")}", icon = custom_icon)
            #layout.prop(item, "enabled", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)
            
class LIST_OT_SelectAll(bpy.types.Operator):
    bl_idname = "my_list.select_all"
    bl_label = "unselect all"
    def execute(self, context):
        for item in context.scene.my_list:
            item.enabled = True
        return{'FINISHED'}
        
class LIST_OT_UnselectAll(bpy.types.Operator):
    bl_idname = "my_list.unselect_all"
    bl_label = "unselect all"
    def execute(self, context):
        for item in context.scene.my_list:
            item.enabled = False
        return{'FINISHED'}
        
class LIST_OT_CopyItem(bpy.types.Operator):
    bl_idname = "my_list.copy_item"
    bl_label = "Add a new item"
    def execute(self, context):
        my_item = context.scene.my_list.add()
        item = context.scene.my_list[context.scene.list_index]
        my_item.id_referenceonly = f"{len(bpy.context.scene.my_list)}"
        my_item.material_name = f"{item["material_name"]}_1"
        my_item.value = item["value"]
        for texture in item.textures:
            my_texture = my_item.textures.add()
            my_texture.texture_slot = texture.texture_slot
            my_texture.texture_image_name = texture.texture_image_name
        return{'FINISHED'}
        
class LIST_OT_ExportItem(bpy.types.Operator, ImportHelper):
    bl_idname = "my_list.export_item"
    bl_label = "Export"
    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Where I will save my stuff"
        # subtype='DIR_PATH' is not needed to specify the selection mode.
        # But this will be anyway a directory path.
        )
    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={"HIDDEN"}
        )
    
    def collectmaterial(self, context):
        material_json = []
        for item in context.scene.my_list:
            if item.enabled == True:
                my_item = json.loads(item["value"])
                my_item["id_referenceonly"] = item["id_referenceonly"]
                my_item["material_name"] = item["material_name"]
                idx=0
                for texture in item.textures:
                    my_item["textures"][idx]["texture_image_name"] = texture.texture_image_name
                    idx=idx+1
                material_json.append(my_item)
        #print("material_json")
        #print(json.dumps(material_json, indent=4))
        return material_json
        
    def collectmetadata(self, context):
        item = context.scene.metadata_list[context.scene.metadata_index]
        gltf_metadata = json.loads(item.value)
        #print("metadata")
        #print(json.dumps(gltf_metadata, indent=4))
        return gltf_metadata
        
    def execute(self, context):
        material_json = self.collectmaterial(context)
        gltf_metadata = self.collectmetadata(context)
        print(self.directory)
        with open(self.directory + '/material_info.json', 'wb') as f:
            f.write(json.dumps(material_json, indent=4).encode("utf-8"))
        with open(os.path.dirname(self.directory)+'.metadata', 'wb') as f:
	        f.write(json.dumps(gltf_metadata, indent=4).encode("utf-8"))
            
        return{'FINISHED'}
        
class LIST_OT_DeleteItem(bpy.types.Operator):
    bl_idname = "my_list.delete_item"
    bl_label = "Deletes an item"
    @classmethod
    def poll(cls, context):
        return context.scene.my_list
    def execute(self, context):
        my_list = context.scene.my_list
        index = context.scene.list_index
        my_list.remove(index)
        context.scene.list_index = min(max(0, index - 1), len(my_list) - 1)
        return{'FINISHED'}
        
class LIST_OT_MoveItem(bpy.types.Operator):
    bl_idname = "my_list.move_item"
    bl_label = "Move an item in the list"
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))
    @classmethod
    def poll(cls, context):
        return context.scene.my_list
    def move_index(self):
        index = bpy.context.scene.list_index
        list_length = len(bpy.context.scene.my_list) - 1 # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        bpy.context.scene.list_index = max(0, min(new_index, list_length))
    def execute(self, context):
        my_list = context.scene.my_list
        index = context.scene.list_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        my_list.move(neighbor, index)
        self.move_index()
        return{'FINISHED'}
        
class LIST_OT_LoadItem(bpy.types.Operator):
    bl_idname = "my_list.load_item"
    bl_label = ""
    def execute(self, context):
        if context.scene.get("kuromdlmetadata") is None:
            print('')
        else:
            context.scene.my_list.clear()
            context.scene.metadata_list.clear()
            my_item = context.scene.metadata_list.add()
            my_item.metadata_name = "（无）"
            for entry in json.loads(context.scene["kuromdlmetadata"]):
                for key in entry.keys():
                    if entry[key]["type"] == "material_struct":
                        for material in entry[key]["data"]:
                            my_item = context.scene.my_list.add()
                            my_item.ref_name = f"{key}"
                            my_item.id_referenceonly = f"{material["id_referenceonly"]}"
                            my_item.material_name = f"{material["material_name"]}"
                            for texture in material["textures"]:
                                my_texture = my_item.textures.add()
                                my_texture.texture_slot = texture["texture_slot"]
                                my_texture.texture_image_name = texture["texture_image_name"]
                            my_item.value = json.dumps(material, indent=4)
                    else:
                        my_item = context.scene.metadata_list.add()
                        my_item.metadata_name = key
                        my_item.value = json.dumps(entry[key]["data"], indent=4)
                        
        return{'FINISHED'}

class FDK_PT_FDKMATERIAL(bpy.types.Panel):
    bl_idname = "KURO_PT_KuroMDL_material"
    bl_label = "KuroMDL Metadata"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FDK_Snippets"
    
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'
    #bl_context = "scene"
    
    @classmethod
    def poll(cls, context):
        return context.scene.my_list and context.scene.active_xbone_subpanel == 'IOTools'
        
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if bpy.context.scene.get("kuromdlmetadata") is None:
            print('')
        else:
            localstorage = json.loads(bpy.context.scene["kuromdlmetadata"])
            
            box = layout.box()
            row = box.row()
            row.operator('my_list.load_item', text='重新加载')
            row.operator('my_list.export_item', text='输出')
            row.label(text='')
            
            box = layout.box()
            row = box.row()
            row.label(text='材质')
            row = box.row()
            row.template_list("P_UL_Material_List", "The_List", scene, "my_list", scene, "list_index")
            row = box.row()
            row.label(text='')
            row.operator('my_list.select_all', text='全选')
            row.operator('my_list.unselect_all', text='全不选')
            row.operator('my_list.copy_item', text='复制')
            #row.operator('my_list.move_item', text='UP').direction = 'UP'
            #row.operator('my_list.move_item', text='DOWN').direction = 'DOWN'
            
            #for entry in localstorage:
                #for key in entry.keys():
                    #if entry[key]["type"] == "material_struct":
                        #for material in entry[key]["data"]:
                            #row = col.row(align=True)
                            #row.label(text=f"{material["id_referenceonly"]}")
                            #row.label(text=material["material_name"])
                            #row.label(text=json.dumps(material))
                            #row = layout.row(align=True)
                            #row.label(text=entry.name)
                            #row.prop(entry, "value", text="")
                            #localstorage[0]["c0010_gltf_metadata"]
            if scene.list_index >= 0 and scene.my_list:
                item = scene.my_list[scene.list_index]
                #box = layout.box()
                col = box.column(align=True)
                col.prop(item, "material_name", text=f"id:{item.id_referenceonly}")
                for texture in item.textures:
                    col.prop(texture, "texture_image_name", text=f"slot: {texture.texture_slot}")
                col = box.column(align=True)
                col.prop(item, "value")

class FDK_PT_FDKMETADATA(bpy.types.Panel):
    bl_idname = "KURO_PT_KuroMDL_metadata"
    bl_label = "KuroMDL Material"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FDK_Snippets"
    
    @classmethod
    def poll(cls, context):
        return context.scene.metadata_list and context.scene.active_xbone_subpanel == 'IOTools'
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if bpy.context.scene.get("kuromdlmetadata") is None:
            print('')
        else:               
            box = layout.box()
            row = box.row()
            row.label(text='元数据')
            row = box.row()
            row.template_list("P_UL_Metadata_List", "The_List2", scene, "metadata_list", scene, "metadata_index")
            
            if scene.metadata_index >= 0 and scene.metadata_list:
                item = scene.metadata_list[scene.metadata_index]
                #box = layout.box()
                col = box.column(align=True)
                col.label(text=f"{item.metadata_name}")
                col.prop(item, "value")
########################## Divider ##########################
class O_CheckMaterialsLocal(bpy.types.Operator):
    bl_idname = "fdktools.check_materials_local"
    bl_label = "比对material_info💡"
    bl_description = "对比工作区的材质和选取的是否一致"
    
    def execute(self, context):
        hasmissing = O_CheckMaterials.processdata(self, context)
        if hasmissing==False:
            ShowMessageBox(f"没有缺少的材质定义")
        else:
            ShowMessageBox(f"请检查输出窗口，将缺少的材质添加到material_info.json")
        self.report({'INFO'}, f"O_CheckMaterialsLocal FINISHED")
        return {'FINISHED'}
    
class O_CheckMaterials(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.check_materials"
    bl_label = "比对material_info"
    bl_description = "选择包含material_info的文件夹，对比工作区的材质和json中的材质是否一致"
    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Where I will save my stuff"
        # subtype='DIR_PATH' is not needed to specify the selection mode.
        # But this will be anyway a directory path.
        )
    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={"HIDDEN"}
        )
    
    def execute(self, context):
        try:
            materials = lib_fmtibvb.read_struct_from_json(self.directory+"/material_info.json")
        except Exception as e:
            self.report({'ERROR'}, f"导入material_info.json文件时出现错误: {e}")
            return {'CANCELLED'}
        hasmissing = self.processdata(context, materials)
        if hasmissing==False:
            ShowMessageBox(f"没有缺少的材质定义")
        else:
            ShowMessageBox(f"请检查输出窗口，将缺少的材质添加到material_info.json")
        self.report({'INFO'}, f"O_CheckMaterials FINISHED")
        return {'FINISHED'}
    
    def processdata(self, context, materials=[]):
        if context.scene.fdk_opt_compare_local == True:
            material_json = []
            for item in context.scene.my_list:
                if item.enabled == True:
                    my_item = json.loads(item["value"])
                    my_item["id_referenceonly"] = item["id_referenceonly"]
                    my_item["material_name"] = item["material_name"]
                    idx=0
                    for texture in item.textures:
                        my_item["textures"][idx]["texture_image_name"] = texture.texture_image_name
                        idx=idx+1
                    material_json.append(my_item)
            materials = material_json
        json_material=["Dots Stroke"]
        for material in materials:
            #self.report({'INFO'}, f"material1:{material["material_name"]}")
            json_material.append(material["material_name"])
        hasmissing=False
        for mat in bpy.data.materials:
            if not mat.name in json_material:
                self.report({'INFO'}, f"缺少的材质:")
                self.report({'INFO'}, f"    {mat.name}")
                for node in mat.node_tree.nodes:
                        for slot_base_color in node.inputs:
                            if slot_base_color.type == "RGBA" and slot_base_color.is_linked:
                                node_base_color = slot_base_color.links[0].from_node
                                if node_base_color.type == "MIX":
                                    for slot_base_color2 in node_base_color.inputs:
                                        if slot_base_color2.is_linked:
                                            node_base_color2 = slot_base_color2.links[0].from_node
                                            if node_base_color2.type == 'TEX_IMAGE':
                                                self.report({'INFO'}, f"        {node_base_color2.image.name}")
                                elif not node_base_color.type == "VERTEX_COLOR":
                                    try:
                                        self.report({'INFO'}, f"        {node_base_color.image.name}")
                                    except:
                                        self.report({'ERROR'},f"        exception:{node_base_color.type}")
                hasmissing = True
        return hasmissing

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
########################## Divider ##########################
class O_ExportVBIB(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.export_to_vbib"
    bl_label = "导出文件夹💡"
    bl_description = "选择文件夹，在其中输出VBIB及JSON"
    #filename_ext = ".*"
    #filter_glob: bpy.props.StringProperty(
    #    default="bpy.context.blend_data.filepath.*",
    #    options={'HIDDEN'},
    #    maxlen=255,  # Max internal buffer length, longer would be clamped.
    #)
    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Where I will save my stuff"
        # subtype='DIR_PATH' is not needed to specify the selection mode.
        # But this will be anyway a directory path.
        )
    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={"HIDDEN"}
        )
    
    def execute(self, context):
        self.export(context, self.directory)
        return {'FINISHED'}
        
    def export(self, context, directory):
        from .io_scene_gltf2.io.com.debug import Log
        from pygltflib import GLTF2
        import logging
        export_settings = self.as_keywords()
        export_settings['gltf_filepath'] = directory
        export_settings['gltf_user_extensions'] = []
        export_settings['gltf_hierarchy_full_collections'] = False
        export_settings['gltf_armature_object_remove'] = False
        export_settings['gltf_flatten_bones_hierarchy'] = False
        export_settings['gltf_flatten_obj_hierarchy'] = False
        export_settings['gltf_leaf_bone'] = False
        export_settings['gltf_animation_mode'] = 'ACTIONS'
        export_settings['gltf_anim_scene_split_object'] = True
        export_settings['gltf_anim_slide_to_zero'] = False
        export_settings['gltf_export_extra_animations'] = False
        export_settings['gltf_merge_animation'] = 'ACTION'
        export_settings['gltf_draco_mesh_compression'] = False
        export_settings['gltf_draco_mesh_compression_level'] = 6
        export_settings['gltf_draco_position_quantization'] = 14
        export_settings['gltf_draco_normal_quantization'] = 10
        export_settings['gltf_draco_texcoord_quantization'] = 12
        export_settings['gltf_draco_color_quantization'] = 10
        export_settings['gltf_draco_generic_quantization'] = 12
        export_settings['gltf_gpu_instances'] = False
        export_settings['gltf_lights'] = False
        export_settings['gltf_lighting_mode'] = 'SPEC'
        export_settings['gltf_morph'] = True
        export_settings['gltf_morph_normal'] = True
        export_settings['gltf_morph_tangent'] = False
        export_settings['gltf_morph_anim'] = True
        export_settings['gltf_unused_textures'] = False
        export_settings['gltf_unused_images'] = False
        export_settings['gltf_visible'] = False
        export_settings['gltf_renderable'] = False
        export_settings['gltf_filedirectory'] = os.path.dirname(export_settings['gltf_filepath']) + '/'
        export_settings['gltf_texturedirectory'] = export_settings['gltf_filedirectory']
        export_settings['gltf_keep_original_textures'] = False
        export_settings['gltf_image_format'] = 'AUTO'
        export_settings['gltf_add_webp'] = False
        export_settings['gltf_webp_fallback'] = False
        export_settings['gltf_image_quality'] = 75
        export_settings['gltf_copyright'] = ''
        export_settings['gltf_texcoords'] = True
        export_settings['gltf_normals'] = True
        export_settings['gltf_tangents'] = True and export_settings['gltf_normals']
        export_settings['gltf_loose_edges'] = False
        export_settings['gltf_loose_points'] = False
        export_settings['gltf_binary'] = bytearray()
        export_settings['gltf_binaryfilename'] = '.bin'
        export_settings['gltf_gn_mesh'] = False
        export_settings['gltf_rest_position_armature'] = True
        export_settings['gltf_frame_step'] = 1
        export_settings['gltf_frame_range'] = False
        export_settings['gltf_force_sampling'] = True
        export_settings['gltf_sampling_interpolation_fallback'] = 'LINEAR'
        export_settings['gltf_optimize_animation'] = True
        export_settings['gltf_optimize_animation_keep_armature'] = True
        export_settings['gltf_optimize_animation_keep_object'] = False
        export_settings['gltf_optimize_disable_viewport'] = False
        export_settings['gltf_selected'] = False
        export_settings['gltf_layers'] = True
        export_settings['gltf_extras'] = False
        export_settings['gltf_yup'] = True
        export_settings['gltf_active_collection'] = False
        export_settings['gltf_active_collection_with_nested'] = True
        export_settings['gltf_active_scene'] = False
        export_settings['gltf_collection'] = ''
        export_settings['gltf_skins'] = True
        export_settings['gltf_all_vertex_influences'] = False
        export_settings['gltf_vertex_influences_nb'] = 4
        export_settings['gltf_apply'] = False
        export_settings['gltf_shared_accessors'] = False
        export_settings['gltf_current_frame'] = False
        export_settings['gltf_animations'] = True
        export_settings['gltf_def_bones'] = False
        export_settings['gltf_materials'] = 'EXPORT'
        export_settings['gltf_attributes'] = False
        export_settings['gltf_cameras'] = False
        export_settings['gltf_loglevel'] = 1
        export_settings['loglevel'] = logging.INFO
        export_settings['log'] = Log(export_settings['loglevel'])
        export_settings['gltf_export_anim_pointer'] = False
        export_settings['gltf_trs_w_animation_pointer'] = False
        export_settings['gltf_export_anim_single_armature'] = True
        export_settings['gltf_vertex_color'] = 'Color'
        export_settings['gltf_all_vertex_colors'] = True
        export_settings['gltf_active_vertex_color_when_no_material'] = True
        export_settings['gltf_bake_animation'] = False
        export_settings['gltf_negative_frames'] = 'SLIDE'
        export_settings['gltf_format'] = 'GLB'
        gltf_data, giant_buffer = gltf2_blender_export(export_settings)
        model_gltf = GLTF2().from_json(json.dumps(gltf_data), infer_missing=True)
        model_gltf.set_binary_blob(giant_buffer)
        metadata = {}
        if context.scene.fdk_opt_compare_local == True:
            if len(context.scene.metadata_list) > context.scene.metadata_index:
                metadata = LIST_OT_ExportItem.collectmetadata(self, context)
            else:
                self.report({'ERROR'}, f"数据不存在: {e}。将忽略metadata。")
            if len(context.scene.my_list) > 0:
                material_json = LIST_OT_ExportItem.collectmaterial(self, context)
                with open(directory + '/material_info.json', 'wb') as f:
                    f.write(json.dumps(material_json, indent=4).encode("utf-8"))
        else:
            try:
                #self.report({'INFO'}, f"load{".".join(self.filepath.split('.')[:-1])+".metadata"}")
                self.report({'INFO'}, f"load{os.path.dirname(directory)+".metadata"}")
                #metadata = lib_fmtibvb.read_struct_from_json(".".join(self.filepath.split('.')[:-1])+".metadata")
                metadata = lib_fmtibvb.read_struct_from_json(os.path.dirname(directory)+".metadata")
            except Exception as e:
                self.report({'ERROR'}, f"文件不存在: {e}。将忽略metadata。")
        #kuro_gltf_to_meshes.process_data(os.path.dirname(self.filepath) + '/' + bpy.path.display_name_from_filepath(self.filepath), model_gltf, metadata, True, True)
        kuro_gltf_to_meshes.process_data(directory, model_gltf, metadata, True, True)
        #self.report({'INFO'}, f"export to {os.path.dirname(self.filepath) + '/' + bpy.path.display_name_from_filepath(self.filepath)}")
        self.report({'INFO'}, f"export to {directory}")
########################## Divider ##########################
class O_ConvertMDL(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_convert"
    bl_label = "MDL to GLB+BIN"
    bl_description = "选取MDL文件，转换为GLB+BIN"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Processing {mdl_file}")
        with open(mdl_file, "rb") as f:
            mdl_data = f.read()
        kuro_mdl_to_basic_gltf.process_mdl(mdl_file, mdl_data, True, False, False, True, True)
        return {'FINISHED'}
########################## Divider ##########################
class O_ExportMDLJson(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_export_json"
    bl_label = "MDL提取JSON"
    bl_description = "选取MDL文件，仅输出2个JSON"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Processing {mdl_file}")
        with open(mdl_file, "rb") as f:
            mdl_data = f.read()
        kuro_mdl_export_meshes.process_mdl(mdl_file, mdl_data, True, False, False, True, True)
        return {'FINISHED'}
########################## Divider ##########################
class O_ExportMDLMetadata(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_export_metadata"
    bl_label = "MDL提取metadata"
    bl_description = "选取MDL文件，仅输出.metadata"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Processing {mdl_file}")
        with open(mdl_file, "rb") as f:
            mdl_data = f.read()
        kuro_mdl_to_basic_gltf.process_mdl(mdl_file, mdl_data, True, False, False, True, True, False, True)
        return {'FINISHED'}
########################## Divider ##########################
class O_ExportMDL(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_export"
    bl_label = "MDL to VBIB+JSON"
    bl_description = "选取MDL文件，输出VBIB及JSON"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Processing {mdl_file}")
        with open(mdl_file, "rb") as f:
            mdl_data = f.read()
        kuro_mdl_export_meshes.process_mdl(mdl_file, mdl_data, True, False, False, True)
        return {'FINISHED'}
########################## Divider ##########################
class O_ImportMDL(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_import"
    bl_label = "导入MDL"
    bl_description = "将MDL转换为GLB数据并直接导入"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        import sys
        usedds = context.scene.fdk_opt_usedds
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
            
        self.report({'INFO'}, f"Processing {mdl_file}")
        with open(mdl_file, "rb") as f:
            mdl_data = f.read()
        
        material_struct = kuro_mdl_export_meshes.obtain_material_data(mdl_data)
        gltf_data, giant_buffer, gltf_metadata = kuro_mdl_to_basic_gltf.process_mdl(mdl_file, mdl_data, True, False, False, True, False, usedds)
        
        if bpy.context.scene.get("kuromdlmetadata") is None:
            bpy.context.scene["kuromdlmetadata"] = "[]"
        
        localstorage = json.loads(bpy.context.scene["kuromdlmetadata"]);
        localstorage.append({
            f"{bpy.path.display_name_from_filepath(mdl_file)}_material_struct":{"data":material_struct,"type":'material_struct'},
            f"{bpy.path.display_name_from_filepath(mdl_file)}_gltf_metadata":{"data":gltf_metadata,"type":'gltf_metadata'}
        })
        
        bpy.context.scene["kuromdlmetadata"] = json.dumps(localstorage)
        LIST_OT_LoadItem.execute(self, context)
        #return {'FINISHED'}
        import_settings = self.as_keywords()
        user_extensions = []
        preferences = bpy.context.preferences
        for addon_name in preferences.addons.keys():
            try:
                module = sys.modules[addon_name]
            except Exception:
                continue
            if hasattr(module, 'glTF2ImportUserExtension'):
                extension_ctor = module.glTF2ImportUserExtension
                user_extensions.append(extension_ctor())
        import_settings['import_user_extensions'] = user_extensions
        import_settings['import_shading'] = "NORMALS"
        
        import_settings['merge_vertices'] = True
        import_settings['import_merge_material_slots'] = True
        
        import_settings['import_pack_images'] = True
        import_settings['import_webp_texture'] = False
        import_settings['import_unused_materials'] = False
        
        import_settings['bone_heuristic'] = "BLENDER"
        import_settings['guess_original_bind_pose'] = True
        import_settings['disable_bone_shape'] = False
        import_settings['bone_shape_scale_factor'] = 1.0
        
        import_settings['import_scene_as_collection'] = True
        import_settings['import_select_created_objects'] = True
        import_settings['import_scene_extras'] = True
        
        gltf_importer=glTFImporter(mdl_file, import_settings)
        gltf_importer.data=gltf_from_dict(gltf_data)
        #self.report({'INFO'}, f"debug: {gltf_importer.data.nodes}")
        gltf_importer.glb_buffer=giant_buffer
        BlenderGlTF.create(gltf_importer)
        
        bpy.ops.object.select_all(action='DESELECT')
        collection = bpy.data.collections.get('glTF_not_exported')
        if not collection is None:
            bpy.data.collections.remove(collection)
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                for bone in obj.pose.bones:
                    bone.custom_shape = None
        
        return {'FINISHED'}
########################## Divider ##########################
class O_GltfToMeshes(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.gltf_to_meshes"
    bl_label = "GLTF to Meshes"
    bl_description = "将GLB转换为VB/IB文件"
    filename_ext = ".glb"
    filter_glob: bpy.props.StringProperty(
        default="*.glb;*.gltf",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择glb/gltf文件")
            return {'CANCELLED'}
        #encodings = ['utf-8', 'gbk', 'utf-16']
        try:
            self.report({'INFO'}, f"{mdl_file}")
            kuro_gltf_to_meshes.process_gltf(mdl_file, True, True)
            #with open(json_file, 'r', newline='', encoding=encoding) as file:
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"导入JSON文件时出现错误1: {e}")
            return {'CANCELLED'}
        return {'CANCELLED'}
########################## Divider ##########################
class O_UpdateMDL(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.mdl_import_vbib"
    bl_label = "文件夹导入MDL💡"
    bl_description = "选取MDL文件，以包含更改后的VBIB及JSON的同名文件夹中的数据更新MDL"
    filename_ext = ".mdl"
    filter_glob: bpy.props.StringProperty(
        default="*.mdl;*.mdl.bak*",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        mdl_file = self.filepath
        kuro_ver = 1
        change_compression = False
        if not mdl_file or not os.path.exists(mdl_file):
            self.report({'ERROR'}, "请选择mdl文件")
            return {'CANCELLED'}
        #encodings = ['utf-8', 'gbk', 'utf-16']
        try:
            with open(mdl_file, "rb") as f:
                mdl_data = f.read()
            if context.scene.fdk_opt_compare_local == False:
                kuro_mdl_import_meshes.process_mdl(mdl_file, mdl_data, self, context, change_compression, kuro_ver, context.scene.fdk_opt_do_not_backup)
                #with open(json_file, 'r', newline='', encoding=encoding) as file:
            else:
                hasmissing = O_CheckMaterials.processdata(self, context)
                if hasmissing==True:
                    ShowMessageBox(f"操作已中断，请检查输出窗口，添加缺少的材质")
                    return {'CANCELLED'}
                else:
                    if mdl_data[0:4] in [b"F9BA", b"C9BA", b"D9BA"]:
                        compressed = True
                        mdl_data = decryptCLE(mdl_data)
                    else:
                        compressed = False
                    if kuro_mdl_export_meshes.obtain_material_data(mdl_data) == False:
                        print("Skipping {0} as it is not a model file.".format(mdl_file))
                        return False
                    
                    if not os.path.exists(mdl_file[:-4]):
                        os.mkdir(mdl_file[:-4])
                        O_ExportVBIB.export(self, context, mdl_file[:-4])
                    elif context.scene.fdk_opt_override_vbib == True:
                        O_ExportVBIB.export(self, context, mdl_file[:-4])
                        
                    skeleton_data = kuro_mdl_import_meshes.build_skeleton_section(kuro_mdl_import_meshes.build_skeleton_struct_from_mdl(mdl_file[:-4]))
                    mesh_data, primitive_data, material_list = kuro_mdl_import_meshes.build_mesh_section(mdl_file[:-4], kuro_ver = kuro_ver)
                    material_data = kuro_mdl_import_meshes.build_material_section(self, context, "", 
                        material_list, kuro_ver, LIST_OT_ExportItem.collectmaterial(self, context))
                    new_mdl_data = kuro_mdl_import_meshes.insert_model_data(mdl_data, skeleton_data, material_data, mesh_data, primitive_data, kuro_ver)
                    # Instead of overwriting backups, it will just tag a number onto the end
                    backup_suffix = ''
                    if context.scene.fdk_opt_do_not_backup == False:
                        if os.path.exists(mdl_file + '.bak' + backup_suffix):
                            backup_suffix = '1'
                            if os.path.exists(mdl_file + '.bak' + backup_suffix):
                                while os.path.exists(mdl_file + '.bak' + backup_suffix):
                                    backup_suffix = str(int(backup_suffix) + 1)
                            shutil.copy2(mdl_file, mdl_file + '.bak' + backup_suffix)
                        else:
                            shutil.copy2(mdl_file, mdl_file + '.bak')
                    if (compressed == True and change_compression == False) or (compressed == False and change_compression == True):
                        new_mdl_data = kuro_mdl_import_meshes.compressCLE(new_mdl_data)
                    with open(mdl_file,'wb') as f:
                        f.write(new_mdl_data)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"导入文件时出现错误: {e}")
            return {'CANCELLED'}
        return {'CANCELLED'}
########################## Divider ##########################
class FDK_PT_Snippets_IO(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_IO"
    bl_label = "I/O"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    
    @classmethod
    def poll(cls, context):
        return context.scene.active_xbone_subpanel == 'IOTools'
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, "fdk_opt_compare_local", text="使用导入的数据💡")
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(O_ImportMDL.bl_idname, icon="IMPORT")#Import MDL
        row.prop(context.scene, "fdk_opt_usedds", text="使用dds贴图")
        col.operator(O_ExportVBIB.bl_idname, icon="EXPORT")#Export VBIB
        
        box = layout.box()
        col = box.column(align=True)
        col.operator(O_UpdateMDL.bl_idname, icon="TRACKING_BACKWARDS")#Import VBIB to MDL
        col.prop(context.scene, "fdk_opt_do_not_backup", text="不创建bak")
        col.prop(context.scene, "fdk_opt_override_vbib", text="使用当前模型")
        if bpy.context.scene.fdk_opt_override_vbib == True:
            col.label(text="⚠如文件夹已存在，将覆盖文件夹内容")
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        if bpy.context.scene.fdk_opt_compare_local == True:
            row.operator(O_CheckMaterialsLocal.bl_idname, icon="MATERIAL")#Compare Material JSON
        else:
            row.operator(O_CheckMaterials.bl_idname, icon="MATERIAL")#Compare Material JSON
        box = layout.box()
        col = box.column(align=True)
        # col.prop(context.scene, "fdk_source_mesh", text="源网格", icon="MESH_DATA")
        # col.prop(context.scene, "fdk_target_mesh", text="目标网格", icon="MESH_DATA")
        # col.operator(O_join_Meshes.bl_idname, text=O_join_Meshes.bl_label, icon="MESH_DATA")
        col.operator(O_ExportMDLJson.bl_idname, icon="TRACKING_FORWARDS")#MDL export JSON
        col.operator(O_ExportMDLMetadata.bl_idname, icon="TRACKING_FORWARDS")#MDL export metadata
        col.operator(O_ExportMDL.bl_idname, icon="FILE_REFRESH")#MDL to VBIB
        col.operator(O_ConvertMDL.bl_idname, icon="FILE_REFRESH")#MDL to GLB+BIN
        col.operator(O_GltfToMeshes.bl_idname, icon="FILE_REFRESH")#GLTF to Meshes
########################## Divider ##########################
classes = [
    TextureItem,
    MaterialListItem,
    MetadataListItem,
    P_UL_Material_List,
    P_UL_Metadata_List,
    LIST_OT_LoadItem,
    LIST_OT_CopyItem,
    LIST_OT_ExportItem,
    LIST_OT_SelectAll,
    LIST_OT_UnselectAll,
    #LIST_OT_DeleteItem,
    #LIST_OT_MoveItem,
    O_ExportVBIB,
    O_ConvertMDL,
    O_ExportMDL,
    O_ExportMDLJson,
    O_ExportMDLMetadata,
    O_GltfToMeshes,
    O_ImportMDL,
    O_UpdateMDL,
    O_CheckMaterials,
    O_CheckMaterialsLocal,
    FDK_PT_Snippets_IO,
    FDK_PT_FDKMATERIAL,
    FDK_PT_FDKMETADATA
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.my_list = bpy.props.CollectionProperty(type = MaterialListItem)
    bpy.types.Scene.list_index = bpy.props.IntProperty(name = "Index for my_list", default = 0)
    
    bpy.types.Scene.metadata_list = bpy.props.CollectionProperty(type = MetadataListItem)
    bpy.types.Scene.metadata_index = bpy.props.IntProperty(name = "Index for metadata_list", default = 0)
    
    bpy.types.Scene.fdk_opt_do_not_backup = bpy.props.BoolProperty(
        name="donot backup",description="导入时不创建bak",default= True
    )
    bpy.types.Scene.fdk_opt_override_vbib = bpy.props.BoolProperty(
        name="donot backup",description="覆盖",default= False
    )
    bpy.types.Scene.fdk_opt_compare_local = bpy.props.BoolProperty(
        name="compare local",description="使用从mdl导入内部的数据。只对带💡的项目有效。",default= True
    )
    bpy.types.Scene.fdk_opt_usedds = bpy.props.BoolProperty(
        name="use dds",description="改用dds",default= True
    )

def unregister():
    del bpy.types.Scene.my_list
    del bpy.types.Scene.list_index
    del bpy.types.Scene.metadata_list
    del bpy.types.Scene.metadata_index
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.fdk_opt_do_not_backup
    del bpy.types.Scene.fdk_opt_override_vbib
    del bpy.types.Scene.fdk_opt_compare_local
    del bpy.types.Scene.fdk_opt_usedds