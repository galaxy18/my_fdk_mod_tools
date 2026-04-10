import bpy,os,json,shutil,mathutils,math,numpy,copy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from mathutils import Vector,Quaternion
from .KuroMDLTools import kuro_mdl_to_basic_gltf, kuro_mdl_import_meshes, kuro_mdl_export_meshes, kuro_gltf_to_meshes, lib_fmtibvb
from .io_scene_gltf2.blender.imp.blender_gltf import BlenderGlTF
from .io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
from .io_scene_gltf2.io.com.gltf2_io import Gltf, gltf_from_dict
from .io_scene_gltf2.blender.exp.export import __export as gltf2_blender_export
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
    
class HelloWorldPanel(bpy.types.Panel):
    bl_idname = "KuroMDLInfos"
    bl_label = "KuroMDL infos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FDK_Snippets"
    
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'
    #bl_context = "scene"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw(self, context):
        layout = self.layout
        if bpy.context.scene.get("kuromdlmetadata") is None:
            print('')
        else:
            localstorage = json.loads(bpy.context.scene["kuromdlmetadata"])
            scene = context.scene
            
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
            
            if scene.list_index >= 0 and scene.my_list:
                item = scene.my_list[scene.list_index]
                #box = layout.box()
                col = box.column(align=True)
                col.prop(item, "material_name", text=f"id:{item.id_referenceonly}")
                for texture in item.textures:
                    col.prop(texture, "texture_image_name", text=f"slot: {texture.texture_slot}")
                col = box.column(align=True)
                col.prop(item, "value")
            
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
        compare_local=context.scene.compare_local
        if compare_local == True:
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
        if context.scene.compare_local == True:
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
        usedds=context.scene.usedds
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
        nobak=context.scene.do_not_backup
        compare_local=context.scene.compare_local
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
            if compare_local == False:
                kuro_mdl_import_meshes.process_mdl(mdl_file, mdl_data, self, context, change_compression, kuro_ver, nobak)
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
                        
                    skeleton_data = kuro_mdl_import_meshes.build_skeleton_section(kuro_mdl_import_meshes.build_skeleton_struct_from_mdl(mdl_file[:-4]))
                    mesh_data, primitive_data, material_list = kuro_mdl_import_meshes.build_mesh_section(mdl_file[:-4], kuro_ver = kuro_ver)
                    material_data = kuro_mdl_import_meshes.build_material_section(self, context, "", 
                        material_list, kuro_ver, LIST_OT_ExportItem.collectmaterial(self, context))
                    new_mdl_data = kuro_mdl_import_meshes.insert_model_data(mdl_data, skeleton_data, material_data, mesh_data, primitive_data, kuro_ver)
                    # Instead of overwriting backups, it will just tag a number onto the end
                    backup_suffix = ''
                    if nobak == False:
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
class ObjType(bpy.types.Operator):
    def is_mesh(scene, obj):
        return obj.type == "MESH"
    def is_armature(scene, obj):
        return obj.type == "ARMATURE"
########################## Divider ##########################
class O_ImportRenameJSON(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.json_rename_import"
    bl_label = "选择重命名配对JSON"
    bl_description = "导入窗口右上角选择编码格式"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        json_file = self.filepath
        if not json_file or not os.path.exists(json_file):
            self.report({'ERROR'}, "请选择有效的JSON文件")
            return {'CANCELLED'}
        # 尝试的编码顺序
        encodings = ['utf-8', 'gbk', 'utf-16']
        for encoding in encodings:
            try:
                with open(json_file, 'r', newline='', encoding=encoding) as file:
                    fdk_rename_pair_json_data=json.load(file)
                    context.scene["fdk_rename_pair_json_data"]=json.dumps(fdk_rename_pair_json_data)
                self.report({'INFO'}, f"JSON文件已导入({encoding}): {json_file}")
                return {'FINISHED'}
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.report({'ERROR'}, f"导入JSON文件时出现错误: {e}")
                return {'CANCELLED'}
        self.report({'ERROR'}, "无法解码JSON文件，请尝试转换为UTF-8编码")
        return {'CANCELLED'}
########################## Divider ##########################
class O_ImportMovingJSON(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.json_moving_import"
    bl_label = "选择重组配置JSON"
    bl_description = "导入窗口右上角选择编码格式"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        json_file = self.filepath
        if not json_file or not os.path.exists(json_file):
            self.report({'ERROR'}, "请选择有效的JSON文件")
            return {'CANCELLED'}
        # 尝试的编码顺序
        encodings = ['utf-8', 'gbk', 'utf-16']
        for encoding in encodings:
            try:
                with open(json_file, 'r', newline='', encoding=encoding) as file:
                    fdk_moving_pair_json_data=json.load(file)
                    context.scene["fdk_moving_pair_json_data"]=json.dumps(fdk_moving_pair_json_data)
                self.report({'INFO'}, f"JSON文件已导入({encoding}): {json_file}")
                return {'FINISHED'}
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.report({'ERROR'}, f"导入JSON文件时出现错误: {e}")
                return {'CANCELLED'}
        self.report({'ERROR'}, "无法解码JSON文件，请尝试转换为UTF-8编码")
        return {'CANCELLED'}
########################## Divider ##########################
class O_ImportJSON(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.json_import"
    bl_label = "选择配置JSON"
    bl_description = "导入窗口右上角选择编码格式"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    def execute(self, context):
        json_file = self.filepath

        if not json_file or not os.path.exists(json_file):
            self.report({'ERROR'}, "请选择有效的JSON文件")
            return {'CANCELLED'}
        # 尝试的编码顺序
        encodings = ['utf-8', 'gbk', 'utf-16']
        for encoding in encodings:
            try:
                with open(json_file, 'r', newline='', encoding=encoding) as file:
                    fdk_config_json_data=json.load(file)
                    context.scene["fdk_config_json_data"]=json.dumps(fdk_config_json_data)
                self.report({'INFO'}, f"JSON文件已导入({encoding}): {json_file}")
                if "CopyBone_arr_base" in fdk_config_json_data:
                    if "change_tail" in fdk_config_json_data["CopyBone_arr_base"]:
                        context.scene.change_tail = fdk_config_json_data["CopyBone_arr_base"]["change_tail"]
                        self.report({'INFO'}, f"change_tail={context.scene.change_tail}")
                    if "change_matrix" in fdk_config_json_data["CopyBone_arr_base"]:
                        context.scene.change_matrix = fdk_config_json_data["CopyBone_arr_base"]["change_matrix"]
                        self.report({'INFO'}, f"change_matrix={context.scene.change_matrix}")
                    if "reset_empty" in fdk_config_json_data["CopyBone_arr_base"]:
                        context.scene.reset_empty = fdk_config_json_data["CopyBone_arr_base"]["reset_empty"]
                        self.report({'INFO'}, f"reset_empty={context.scene.reset_empty}")
                warning = ""
                keys = ["CopyBone_arr_base","CopyBone_arr_names",
                    "CopyBone_arr_ignore","CopyBone_arr_add",
                    "CopyBone_arr_add_ignore","AddEmpty_arr_addPoint",
                    "RenameBone_arr_copy","RenameBone_arr_ignore","RemoveBone_arr_shouldKeep"]
                missingkey=False
                for key in keys:
                    if not key in fdk_config_json_data or not "data" in fdk_config_json_data[key]:
                        warning+=key+", "
                        missingkey=True
                if missingkey:
                    self.report({'INFO'}, f"JSON文件已导入({encoding}): {json_file};"+
                    f"但缺少{warning}字段；建议检查JSON文件后重新导入")
                else:
                    self.report({'INFO'}, f"JSON文件已导入({encoding}): {json_file}")
                    if "RenameBone_arr_copy" in fdk_config_json_data:
                        if "Headkey" in fdk_config_json_data["RenameBone_arr_copy"] \
                            and (not fdk_config_json_data["RenameBone_arr_copy"]["Headkey"]==""):
                            context.scene.fdk_modify_headname=fdk_config_json_data["RenameBone_arr_copy"]["Headkey"]
                        if "RenameBone_prefix" in fdk_config_json_data["RenameBone_arr_copy"] \
                            and (not fdk_config_json_data["RenameBone_arr_copy"]["RenameBone_prefix"]==""):
                            context.scene.fdk_rename_prefix=fdk_config_json_data["RenameBone_arr_copy"]["RenameBone_prefix"]
                        # if "RenameBone_copy_prefix" in fdk_config_json_data["RenameBone_arr_copy"]:
                            # context.scene.fdk_rename_copy_prefix=fdk_config_json_data["RenameBone_arr_copy"]["RenameBone_copy_prefix"]
                        if "RenameBone_orig_prefix" in fdk_config_json_data["RenameBone_arr_copy"] \
                            and (not fdk_config_json_data["RenameBone_arr_copy"]["RenameBone_orig_prefix"]==""):
                            context.scene.fdk_rename_orig_prefix=fdk_config_json_data["RenameBone_arr_copy"]["RenameBone_orig_prefix"]
                return {'FINISHED'}
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.report({'ERROR'}, f"导入JSON文件时出现错误: {e}")
                return {'CANCELLED'}
        self.report({'ERROR'}, "无法解码JSON文件，请尝试转换为UTF-8编码")
        return {'CANCELLED'}
########################## Divider ##########################
class O_DelOtherBone(bpy.types.Operator):
    bl_idname = "fdktools.remove_other_bones"
    bl_label = "删除其他骨骼"
    bl_description = "根据所输入父级骨骼名字删除目标骨架中的其以外的骨骼"
    
    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey is None or headkey == "":
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if arm.edit_bones.get(headkey) is not None:
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            bpy.ops.armature.select_all(action='INVERT')
            bpy.ops.armature.delete()
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            self.report({'INFO'}, f"所选骨架中不存在{headkey}")
            return {'FINISHED'}
        self.report({'INFO'},f"O_DelOtherBone finished")
        return {'FINISHED'}

class O_DelBone(bpy.types.Operator):
    bl_idname = "fdktools.remove_head_bones"
    bl_label = "删除所有子骨骼"
    bl_description = "根据所输入父级骨骼名字删除目标骨架中的其所有子骨骼"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey is None or headkey == "":
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if arm.edit_bones.get(headkey) is not None:
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            arm.edit_bones[headkey].select=False
            bpy.ops.armature.delete()
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            self.report({'INFO'}, f"所选骨架中不存在{headkey}")
            return {'FINISHED'}
        self.report({'INFO'},f"O_DelBone finished")
        return {'FINISHED'}

class O_RenameBone(bpy.types.Operator):
    bl_idname = "fdktools.rename_head_bones"
    bl_label = "重命名脸部顶点组"
    bl_description = "根据所输入父级骨骼名字重命名目标骨架中的子级，根据JSON配置复制一份原名骨骼以应对定位"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        rename_prefix=context.scene.fdk_rename_prefix
        rename_copy_prefix="_Copy"
        rename_orig_prefix=context.scene.fdk_rename_orig_prefix
        if rename_prefix=="":
            rename_prefix="_New"
            self.report({'INFO'}, "RenameBone_prefix 是空的；自动重置为默认值_New")
        if rename_orig_prefix=="":
            rename_orig_prefix="_Orig"
            self.report({'INFO'}, "RenameBone_orig_prefix 是空的；自动重置为默认值_Orig")
        if rename_copy_prefix == rename_prefix or rename_copy_prefix == rename_orig_prefix:
            rename_copy_prefix="_Copying"
        if not "fdk_config_json_data" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            try:
                arr_copy=json.loads(context.scene["fdk_config_json_data"])["RenameBone_arr_copy"]["data"]
                arr_ignore=json.loads(context.scene["fdk_config_json_data"])["RenameBone_arr_ignore"]["data"]
            except:
                self.report({'ERROR'}, "无效的配置JSON；"+
                "请检查RenameBone_arr_copy和RenameBone_arr_ignore。将不会复制定位骨骼")
                arr_copy=[]
                arr_ignore=[]
        self.report({'INFO'}, f"O_RenameBone：父级：{headkey}")
                
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        bpy.ops.object.mode_set(mode='EDIT')
        newbones=[]
        for bonename in arr_copy:
            bpy.ops.armature.select_all(action='DESELECT')
            try:
                if arm.edit_bones.get(bonename) is None:
                    self.report({'INFO'}, f"Bone {bonename} not found in current armature;skipped")
                else:
                    self.report({'INFO'}, "copying "+bonename)
                    arm.edit_bones.active = arm.edit_bones[bonename]
                    self.report({'INFO'}, bpy.context.selected_editable_bones[0].name)
                    b = bpy.context.selected_editable_bones[0]
                    cb = arm.edit_bones.new(f"{bonename}{rename_copy_prefix}")
                    cb.head = b.head
                    cb.tail = b.tail
                    cb.matrix = b.matrix
                    cb.parent = b.parent
                    newbones.append(cb)
                    if headkey=="":
                        arm.edit_bones[bonename].name=f"{bonename}{rename_orig_prefix}"
                    
            except Exception as e: self.report({'INFO'}, e)
            
        if not headkey=="":
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            for obj in bpy.context.selected_editable_bones:
                if not (obj.name in arr_ignore or obj.name.endswith(rename_copy_prefix) 
                or obj.name.endswith(rename_prefix) or obj.name.endswith(rename_orig_prefix)):
                    oldname = obj.name
                    obj.name = f"{oldname}{rename_prefix}"
                    
        for obj in newbones:
            obj.name = obj.name.replace(rename_copy_prefix, "")

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_RenameBone finished")
        return {'FINISHED'}

class O_AddEmpty(bpy.types.Operator):
    bl_idname = "fdktools.add_empty_objects"
    bl_label = "按JSON添加空物体"
    bl_description = "按JSON添加空物体。配置中父级为骨架的将设为目标骨架"
    
    def execute(self, context):
        if not "fdk_config_json_data" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            try:
                arr_addPoint=json.loads(context.scene["fdk_config_json_data"])["AddEmpty_arr_addPoint"]["data"]
            except:
                self.report({'ERROR'}, "无效的配置JSON；请检查AddEmpty_arr_addPoint。")
                return {'FINISHED'}
                
        needArm=False
        for obj in arr_addPoint:
            if obj[1]=="" and obj[2]=="BONE":
                needArm=True
        if needArm:
            parentobj = bpy.data.objects.get(bpy.context.active_object.name)
            arm = parentobj.data
            
        for obj in arr_addPoint:
            if not obj[0] in bpy.data.objects:
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")
                #bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD", location=(0, 0, 0), scale=(1, 1, 1))
                #ae = bpy.context.active_object
                emptyobj = bpy.data.objects.new( obj[0], None )
                # due to the new mechanism of "collection"
                bpy.context.scene.collection.objects.link(emptyobj)
                # empty_draw was replaced by empty_display
                emptyobj.empty_display_size = 2
                emptyobj.empty_display_type = 'PLAIN_AXES'   
                #bpy.context.active_object.name = obj[0]
                if obj[2] == "BONE":
                    emptyobj.parent = parentobj
                    emptyobj.parent_type = "BONE"
                    if obj[3] in arm.bones:
                        emptyobj.parent_bone = obj[3]
                        emptyobj.location = arm.bones[obj[3]].head
                    else:
                        self.report({'ERROR'}, obj[0]+": parent bone "+obj[3]+" not exist")
                elif obj[1] in bpy.data.objects:
                    emptyobj.parent = bpy.data.objects[obj[1]]
                    emptyobj.parent_type = obj[2]
                else:
                    self.report({'INFO'}, obj[0]+": parent node "+obj[1]+" not exist;skipped")
                #math.sin(math.pi/4)
                emptyobj.rotation_mode = "QUATERNION"
                #emptyobj.rotation_quaternion = Quaternion([math.sin(math.pi/4),-math.sin(math.pi/4),0,0])
                emptyobj.rotation_quaternion = Quaternion([1,0,0,0])
                emptyobj.scale = [1.0,1.0,1.0]
                #emptyobj.lock_scale = [True,True,True]
            else:
                self.report({'INFO'}, obj[0]+": "+obj[0]+" already exists;skipped")
        self.report({'INFO'},f"O_AddEmpty finished")
        return {'FINISHED'}

class O_CopyBone(bpy.types.Operator):
    bl_idname = "fdktools.copy_bone_nodes"
    bl_label = "根据JSON配置复制位置"
    bl_description = "根据JSON配置复制源骨架的位置到目标骨架"

    def create_Bone(_console, _context, arm0, arm, b_orig):
        resetempty=_context.scene["reset_empty"]
        try:
            arr_add_ignore = json.loads(_context.scene["fdk_config_json_data"])["CopyBone_arr_add_ignore"]["data"]
        except:
            arr_add_ignore=[]
        if (arm.edit_bones.get(b_orig.name) is None) and (not b_orig.name in arr_add_ignore):
            _console.report({'INFO'}, '    creating '+b_orig.name)
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if arm.edit_bones.get(b_orig.parent.name) is None:
                O_CopyBone.create_Parent(arm0, arm, b_orig.parent)
            b.parent = arm.edit_bones[b_orig.parent.name]
            for child in b_orig.children:
                # _console.report({'INFO'}, '    child:'+child.name)
                O_CopyBone.create_Bone(_console, _context, arm0, arm, child)
        # _console.report({'INFO'}, '    processing children of'+b_orig.name)
        #重置空物体旋转
        if resetempty == True:
            for obj in bpy.data.objects:
                if obj.parent_type=='BONE' and obj.parent_bone == b_orig.name and obj.type == "EMPTY":
                    obj.rotation_quaternion = Quaternion([1,0,0,0])
                    obj.scale = [1.0,1.0,1.0]

    def create_Parent(arm0, arm, b_orig):
        changematrix=_context.scene["changematrix"]
        _console.report({'INFO'}, '        Info: creating parent bone '+b_orig.name+' can not be skipped')
        if arm.edit_bones.get(b_orig.name) is None:
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            if changematrix==True:
                b.matrix = b_orig.matrix
            if arm.edit_bones.get(b_orig.parent.name) is None:
                O_CopyBone.create_Parent(arm0, arm, b_orig.parent)
            b.parent = arm.edit_bones[b_orig.parent.name]

    def processname(_console, _context, arm0, arm, b_child, processchild=True):
        changematrix=_context.scene["change_matrix"]
        resetempty=_context.scene["reset_empty"]
        changetail=_context.scene["change_tail"]
        try:
            arr_ignore = json.loads(_context.scene["fdk_config_json_data"])["CopyBone_arr_ignore"]["data"]
        except:
            arr_ignore=[]
        changes=mathutils.Vector((0,0,0))
        try:
            if arm.edit_bones.get(b_child.name) is None:
                O_CopyBone.create_Bone(_console, _context, arm0, arm, b_child)
            elif not b_child.name in arr_ignore:
                _console.report({'INFO'}, "Moving bone "+b_child.name)
                b=arm.edit_bones[b_child.name]
                changes=mathutils.Vector((b.head[0]-b_child.head[0],
                    b.head[1]-b_child.head[1],
                    b.head[2]-b_child.head[2]))
                #_console.report({'INFO'}, f"changes: {changes}")
                if changetail == True:
                    b.tail = b.tail-changes
                else:
                    b.tail = b_child.tail
                b.head = b_child.head
                if changematrix==True:
                    b.matrix = b_child.matrix
                if not b_child.parent is None:
                    b.parent = b_child.parent
            if resetempty == True:
                for obj in bpy.data.objects:
                    if obj.parent_type=='BONE' and obj.parent_bone == b_child.name and obj.type == "EMPTY":
                        _console.report({'INFO'}, f"    Moving EMPTY obj: {obj.name} {changes}")
                        obj.rotation_quaternion = Quaternion([1,0,0,0])
                        obj.scale = [1.0,1.0,1.0]
                        obj.location += changes
        except Exception as e: _console.report({'INFO'}, f"{e}")
        if processchild:
            for child in b_child.children:
                O_CopyBone.processname(_console, _context, arm0, arm, child)

    def execute(self, context):
        if not "fdk_config_json_data" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            try:
                arr_add_ignore = json.loads(context.scene["fdk_config_json_data"])["CopyBone_arr_add_ignore"]["data"]
            except:
                self.report({'INFO'}, "无效的配置JSON；CopyBone_arr_add_ignore。将忽略此配置")
            try:
                arr_ignore = json.loads(context.scene["fdk_config_json_data"])["CopyBone_arr_ignore"]["data"]
            except:
                self.report({'INFO'}, "无效的配置JSON；CopyBone_arr_ignore。将忽略此配置")
            try:
                arr_base=json.loads(context.scene["fdk_config_json_data"])["CopyBone_arr_base"]["data"]
            except:
                self.report({'INFO'}, "无效的配置JSON；CopyBone_arr_base。将忽略此配置")
                arr_base=[]
            try:
                arr_names=json.loads(context.scene["fdk_config_json_data"])["CopyBone_arr_names"]["data"]
            except:
                self.report({'INFO'}, "无效的配置JSON；CopyBone_arr_names。将忽略此配置")
                arr_names=[]
            try:
                arr_add=json.loads(context.scene["fdk_config_json_data"])["CopyBone_arr_add"]["data"]
            except:
                self.report({'INFO'}, "无效的配置JSON；CopyBone_arr_add。将忽略此配置")
                arr_add=[]
        try:
            changematrix=context.scene["change_matrix"]
        except:
            context.scene["change_matrix"]=False
        try:
            resetempty=context.scene["reset_empty"]
        except:
            context.scene["reset_empty"]=True
        try:
            changetail=context.scene["change_tail"]
        except:
            context.scene["change_tail"]=True
                
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        arm0=None
        for obj in bpy.context.selected_objects:
            if obj.type=="ARMATURE" and obj.name != bpy.context.active_object.name:
                arm0=obj.data
        if arm0 is None:
            self.report({'ERROR'}, "没有选择对象骨架")
            return {'FINISHED'}

        bpy.ops.object.mode_set(mode='EDIT')
        for basename in arr_base:
            if basename in arm0.edit_bones:
                self.report({'INFO'}, "Process arr_base:"+basename)
                O_CopyBone.processname(self, context, arm0, arm, arm0.edit_bones[basename])
            else:
                self.report({'INFO'}, "arr_base:"+basename+" not exist in source armature")
            
        for basename in arr_names:
            if basename in arm0.edit_bones:
                self.report({'INFO'}, "Process arr_names:"+basename)
                O_CopyBone.processname(self, context, arm0, arm, arm0.edit_bones[basename],False)
            else:
                self.report({'INFO'}, "arr_names:"+basename+" not exist in source armature")
            
        for basename in arr_add:
            if basename in arm0.edit_bones:
                self.report({'INFO'}, "Process arr_add:"+basename)
                O_CopyBone.create_Bone(self, context, arm0, arm, arm0.edit_bones.get(basename))
            else:
                self.report({'INFO'}, "arr_add:"+basename+" not exist in source armature")
                
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_CopyBone finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_AssignArmature(bpy.types.Operator):
    bl_idname = "fdktools.assign_armature"
    bl_label = "根据当前选取状态设置骨架"
    bl_description = "需要先选源骨架，再Ctrl选目标骨架"
    def execute(self, context):
        try:
            if bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
                for (idx, obj) in enumerate(bpy.context.selected_objects):
                    if not obj.name == bpy.context.active_object.name and obj.type == "ARMATURE":
                        context.scene.fdk_source_armature=bpy.context.selected_objects[idx]
        except:
            return {'FINISHED'}
        return {'FINISHED'}
########################## Divider ##########################
class O_RenameByJSON(bpy.types.Operator):
    bl_idname = "fdktools.rename_by_json"
    bl_label = "根据JSON重命名"
    bl_description = "根据JSON重命名目标骨架中的骨骼"
    
    def execute(self, context):
        if not "fdk_rename_pair_json_data" in context.scene or context.scene["fdk_rename_pair_json_data"] == "":
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        rename_pair=json.loads(context.scene["fdk_rename_pair_json_data"])
        arm=bpy.data.objects.get(bpy.context.active_object.name).data
        idx=0
        names=[]
        for key in rename_pair:
            # self.report({'INFO'},f"{key}:{rename_pair[key]}")
            if key in arm.bones:
                b = arm.bones[key]
                b.name = f"renaming{idx}"
                names.append(rename_pair[key])
                idx+=1
        idx=0
        for name in names:
            b=arm.bones[f"renaming{idx}"]
            b.name = name
            idx+=1
            
        self.report({'INFO'},f"O_RenameByJSON finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_MoveByJSON(bpy.types.Operator):
    bl_idname = "fdktools.move_by_json"
    bl_label = "根据JSON重组"
    bl_description = "根据JSON修改目标骨架父子级关系"
    
    def execute(self, context):
        if not "fdk_moving_pair_json_data" in context.scene or context.scene["fdk_moving_pair_json_data"] == "":
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        moving_pair=json.loads(context.scene["fdk_moving_pair_json_data"])
        bpy.ops.object.mode_set(mode='EDIT')
        arm=bpy.data.objects.get(bpy.context.active_object.name).data
        if not 'dummy' in arm.edit_bones:
            dummy = arm.edit_bones.new('dummy')
            dummy.tail.z=1
        if not 'world' in arm.edit_bones:
            world = arm.edit_bones.new('world')
            world.tail.z=1
        if not 'ChrExport' in arm.edit_bones:
            ChrExport = arm.edit_bones.new('ChrExport')
            ChrExport.tail.z=1
            if 'root' in arm.edit_bones:
                ChrExport.tail = arm.edit_bones['root'].head
        if not 'Up_Point' in arm.edit_bones:
            Up_Point = arm.edit_bones.new('Up_Point')
            Up_Point.parent = ChrExport
            if 'upperbody_jo' in arm.edit_bones:
                Up_Point.tail = arm.edit_bones['upperbody_jo'].tail
            if 'root' in arm.edit_bones:
                arm.edit_bones['root'].parent = Up_Point
        
        for pair in moving_pair:
            if pair[0] in arm.edit_bones:
                if pair[1] in arm.edit_bones:
                    arm.edit_bones[pair[0]].parent=arm.edit_bones[pair[1]]
                else:
                    self.report({'INFO'},f"parent {pair[1]} not found")
            else:
                self.report({'INFO'},f"child {pair[0]} not found")
            
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_MoveByJSON finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_hideEmpty(bpy.types.Operator):
    bl_idname = "fdktools.hide_empty_object"
    bl_label = "隐藏空物体"
    bl_description = "隐藏空物体"
    
    def execute(self, context):
        # bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.type == "EMPTY":
                obj.hide_set(True)
                
        self.report({'INFO'},f"O_hideEmpty finished")
        return {'FINISHED'}

class O_showEmpty(bpy.types.Operator):
    bl_idname = "fdktools.unhide_empty_object"
    bl_label = "取消隐藏空物体"
    bl_description = "取消隐藏空物体"
    
    def execute(self, context):
        #bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.type == "EMPTY":
                obj.hide_set(False)
                
        self.report({'INFO'},f"O_showEmpty finished")
        return {'FINISHED'}

class O_delEmpty(bpy.types.Operator):
    bl_idname = "fdktools.remove_empty_object"
    bl_label = "⚠移除空物体"
    bl_description = "移除空物体，会导致丢失配件，如需要保留请勿使用此功能"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == "EMPTY":
                obj.hide_set(False)
                obj.select_set(True)
        
        bpy.ops.object.delete()
        self.report({'INFO'},f"O_delEmpty finished")
        return {'FINISHED'}

class O_resetEmptyRot1(bpy.types.Operator):
    bl_idname = "fdktools.reset_empty_object1"
    bl_label = "空物体旋转0,0"
    bl_description = "重设空物体旋转为1,0,0,0。请确保选取了空物体并可见，否则无效果"
    
    def execute(self, context):
        if bpy.context.active_object:
            if bpy.context.active_object.type == "EMPTY":
                emptyobj=bpy.data.objects[bpy.context.active_object.name]
                emptyobj.rotation_mode = "QUATERNION"
                #emptyobj.rotation_quaternion = Quaternion([math.sin(math.pi/4),-math.sin(math.pi/4),0,0])
                emptyobj.rotation_quaternion = Quaternion([1,0,0,0])
                emptyobj.scale = [1.0,1.0,1.0]
                self.report({'INFO'},f"O_resetEmptyRot finished")
            else:
                self.report({'INFO'},f"物体类型不为EMPTY")
        else:
            self.report({'INFO'},f"请切换编辑模式并令物体可见")
        return {'FINISHED'}

class O_resetEmptyRot2(bpy.types.Operator):
    bl_idname = "fdktools.reset_empty_object2"
    bl_label = "空物体旋转90,-90"
    bl_description = "重设空物体旋转为90,-90,0,0。请确保选取了空物体并可见，否则无效果"
    
    def execute(self, context):
        if bpy.context.active_object:
            if bpy.context.active_object.type == "EMPTY":
                emptyobj=bpy.data.objects[bpy.context.active_object.name]
                emptyobj.rotation_mode = "QUATERNION"
                emptyobj.rotation_quaternion = Quaternion([math.sin(math.pi/4),-math.sin(math.pi/4),0,0])
                emptyobj.scale = [1.0,1.0,1.0]
                self.report({'INFO'},f"O_resetEmptyRot finished")
            else:
                self.report({'INFO'},f"物体类型不为EMPTY")
        else:
            self.report({'INFO'},f"请切换编辑模式并令物体可见")
        return {'FINISHED'}

class O_copyEmptyRot(bpy.types.Operator):
    bl_idname = "fdktools.copy_empty_rotation"
    bl_label = "复制空物体旋转缩放"
    bl_description = "请确保选取了空物体，否则无效果"
    
    def execute(self, context):
        if (not bpy.context.active_object) or (len(bpy.context.selected_objects)!=2) or (bpy.context.selected_objects[0].type != "EMPTY") or (bpy.context.selected_objects[1].type != "EMPTY"):
            return {'CANCELLED'}
        target = bpy.data.objects[bpy.context.active_object.name]
        # source.hide_set(False)
        # target.hide_set(False)
        for obj in bpy.context.selected_objects:
            if obj.name != target.name:
                source = obj
        target.rotation_quaternion = source.rotation_quaternion
        target.scale = source.scale
        self.report({'INFO'},f"copy_empty_rotation finished")
        return {'FINISHED'}

class O_del_glTF_not(bpy.types.Operator):
    bl_idname = "fdktools.remove_gltf_collection"
    bl_label = "清理glTF_not_exported"
    bl_description = "清理glTF_not_exported"
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        collection = bpy.data.collections.get('glTF_not_exported')
        if not collection is None:
            bpy.data.collections.remove(collection)
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                for bone in obj.pose.bones:
                    bone.custom_shape = None
        self.report({'INFO'},f"O_del_glTF_not finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_remove_Empty_Bone(bpy.types.Operator):
    bl_idname = "fdktools.remove_bone_by_meshes"
    bl_label = "⚠清理骨骼"
    bl_description = "（实验功能）删除无顶点组的骨骼；会忽略RemoveBone_arr_shouldKeep中的名称和_Point结尾的名称"
    
    def process(arm,bone,bones,arr_shouldkeep):
        if (not bone.name in bones) or (bone.name in arr_shouldkeep) or (bone.name.endswith("_Point")):
            return False
        else:
            shouldremove = True
            for child in bone.children:
                shouldremove = shouldremove and O_remove_Empty_Bone.process(arm,child,bones,arr_shouldkeep)
            if shouldremove:
                bone.select = True
                bone.select_head = True
                bone.select_tail = True
            return shouldremove
    
    def execute(self, context):
        bpy.context.window_manager.clipboard=""
        meshes=[]
        vgnames = []
        bones = []
        if bpy.context.active_object.type == 'MESH':
            baseobj = bpy.context.active_object.parent
        else:
            baseobj = bpy.context.active_object
        arm = bpy.data.objects.get(baseobj.name).data
        try:
            arr_shouldkeep=json.loads(context.scene["fdk_config_json_data"])["RemoveBone_arr_shouldKeep"]["data"]
        except:
            arr_shouldkeep=[]
        remove_no_child_only = json.loads(context.scene["fdk_config_json_data"])["RemoveBone_arr_shouldKeep"]["remove_no_child_only"]==True
        
        self.report({'INFO'},f"O_remove_Empty_Bone collecting...")
        for obj in bpy.data.objects:
            if obj.type=="MESH" and (not obj.parent is None) and obj.parent.name == baseobj.name:
                meshes.append(obj)
        for mesh in meshes:
            for vg in mesh.vertex_groups:
                if not vg.name in vgnames:
                    vgnames.append(vg.name)
        for bone in arm.bones:
            if not bone.name in vgnames:
                bones.append(bone.name)
        bpy.context.view_layer.objects.active = baseobj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        self.report({'INFO'},f"O_remove_Empty_Bone collect done")
        self.report({'INFO'},f"O_remove_Empty_Bone remove_no_child_only={remove_no_child_only}")
        for bone in arm.edit_bones:
            if remove_no_child_only:
                O_remove_Empty_Bone.process(arm,bone,bones,arr_shouldkeep)
            else:
                if bone.name in bones:
                    if (bone.name in arr_shouldkeep) or bone.name.endswith("_Point"):
                        self.report({'INFO'},f"{bone.name} keeped")
                    else:
                        bone.select = True
                        bone.select_head = True
                        bone.select_tail = True
                        self.report({'INFO'},f"{bone.name} selected")
        bpy.ops.armature.delete()
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_remove_Empty_Bone finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_copy_Bone_Pos(bpy.types.Operator):
    bl_idname = "fdktools.copy_bonepos"
    bl_label = "复制骨节位置"
    bl_description = "在编辑模式选中两段骨节复制位置"
    def execute(self, context):
        if not bpy.context.object.mode == 'EDIT':
            self.report({'ERROR'},f"必须是编辑模式")
            return {'CANCELLED'}
        if not len(bpy.context.selected_editable_bones) ==2:
            self.report({'ERROR'},f"必须选中两段骨节")
            return {'CANCELLED'}
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        b1=bpy.context.active_bone
        for b in bpy.context.selected_editable_bones:
            if b.name != b1.name:
                b0=b
        #create backup
        b = arm.edit_bones.new(b1.name+'_move_backup')
        b.head = b1.head
        b.tail = b1.tail
        b.matrix = b1.matrix
        if not b1.parent == None:
            b.parent = b1.parent
        changes=b0.head - b1.head
        b1.tail = b1.tail+changes
        b1.head = b1.head+changes
        self.report({'INFO'},f"copy_bonepos finished")
        return {'FINISHED'}
class O_copy_Bone_Pos2(bpy.types.Operator):
    bl_idname = "fdktools.copy_bonepos2"
    bl_label = "复制骨节位置2"
    bl_description = "在编辑模式选中两段骨节复制位置，不移动尾端"
    def execute(self, context):
        if not bpy.context.object.mode == 'EDIT':
            self.report({'ERROR'},f"必须是编辑模式")
            return {'CANCELLED'}
        if not len(bpy.context.selected_editable_bones) ==2:
            self.report({'ERROR'},f"必须选中两段骨节")
            return {'CANCELLED'}
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        b1=bpy.context.active_bone
        for b in bpy.context.selected_editable_bones:
            if b.name != b1.name:
                b0=b
        #create backup
        b = arm.edit_bones.new(b1.name+'_backup')
        b.head = b1.head
        b.tail = b1.tail
        b.matrix = b1.matrix
        if not b1.parent == None:
            b.parent = b1.parent
        changes=b0.head - b1.head
        b1.head=b1.head+changes
        self.report({'INFO'},f"copy_bonepos2 finished")
        return {'FINISHED'}
class O_copy_Bone_Pos3(bpy.types.Operator):
    bl_idname = "fdktools.copy_bonepos3"
    bl_label = "复制骨节位置3"
    bl_description = "在编辑模式选中两段骨节复制位置，复制matrix"
    def execute(self, context):
        if not bpy.context.object.mode == 'EDIT':
            self.report({'ERROR'},f"必须是编辑模式")
            return {'CANCELLED'}
        if not len(bpy.context.selected_editable_bones) ==2:
            self.report({'ERROR'},f"必须选中两段骨节")
            return {'CANCELLED'}
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        b1=bpy.context.active_bone
        for b in bpy.context.selected_editable_bones:
            if b.name != b1.name:
                b0=b
        #create backup
        b = arm.edit_bones.new(b1.name+'_backup')
        b.head = b1.head
        b.tail = b1.tail
        b.matrix = b1.matrix
        if not b1.parent == None:
            b.parent = b1.parent
        b1.matrix = b0.matrix
        self.report({'INFO'},f"copy_bonepos3 finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_copy_Armatures(bpy.types.Operator):
    bl_idname = "fdktools.copy_arms"
    bl_label = "补充结构"
    bl_description = "直接补充缺少的结构，不读取json配置"
    
    def execute(self, context):
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        arm0=None
        for obj in bpy.context.selected_objects:
            if obj.type=="ARMATURE" and obj.name != bpy.context.active_object.name:
                arm0=obj.data
        bpy.ops.object.mode_set(mode='EDIT')
        bnew=[]
        for b_orig in arm0.edit_bones:
            if not b_orig.name in arm.edit_bones:
                self.report({'INFO'},'Creating '+b_orig.name)
                b = arm.edit_bones.new(b_orig.name)
                b.head = b_orig.head
                b.tail = b_orig.tail
                b.matrix = b_orig.matrix
                bnew.append(b)
        for b_orig in bnew:
            if arm0.edit_bones[b_orig.name].parent:
                b_orig.parent = arm.edit_bones[arm0.edit_bones[b_orig.name].parent.name]
            for child in arm0.edit_bones[b_orig.name].children:
                self.report({'INFO'},f'Attaching {child.name} to {b_orig.name}')
                arm.edit_bones[child.name].parent=b_orig
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_copy_Armatures finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_attach_Armatures(bpy.types.Operator):
    bl_idname = "fdktools.attach_bones"
    bl_label = "Attach"
    bl_description = "添加到选中骨骼做子级"
    
    #https://stackoverflow.com/questions/2556108/rreplace-how-to-replace-the-last-occurrence-of-an-expression-in-a-string
    def rreplace(s, old, new, occurrence):
        li = s.rsplit(old, occurrence)
        return new.join(li)
    
    def execute(self, context):
        #bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL')
        #put cursor at origin 
        try:
            bpy.context.scene.cursor.location = Vector((0.0, 0.0, 0.0))
            bpy.context.scene.cursor.rotation_euler = Vector((0.0, 0.0, 0.0))
            with bpy.context.temp_override(selected_editable_objects=bpy.context.selected_objects):
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        except Exception as e: self.report({'INFO'}, f"{e}")
            
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        arm0=None
        for obj in bpy.context.selected_objects:
            if obj.type=="ARMATURE" and obj.name != bpy.context.active_object.name:
                obj0=obj
                arm0=obj0.data
                
        #bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in arm0.edit_bones:
            bone.select = False
            bone.select_head = False
            bone.select_tail = False
        if len(bpy.context.selected_bones)==0:
            parentname = O_attach_Armatures.rreplace(arm0.name, '_m', '', 1)
            if parentname in arm.edit_bones:
                parent = arm.edit_bones[parentname]
            else:
                self.report({'INFO'},f"没选择骨节")
                return {'CANCELLED'}
        else:
            parent = bpy.context.selected_bones[0]
        if parent is None:
            self.report({'INFO'},f"没选择骨节")
            return {'CANCELLED'}
        else:
            self.report({'INFO'},f"父级：{parent.name}")
        
        for b_orig in arm0.edit_bones:
            self.report({'INFO'},f"createing {b_orig.name}")
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if b_orig.parent is None:
                b.parent = parent
            else:
                b.parent = arm.edit_bones[b_orig.parent.name]
            
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_attach_Armatures finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_attach_Armatures2(bpy.types.Operator):
    bl_idname = "fdktools.attach_bones2"
    bl_label = "Attach2"
    bl_description = "添加到选中骨骼做子级"
    
    def execute(self, context):
        #bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL')
        #put cursor at origin 
        obj1= bpy.data.objects.get(bpy.context.active_object.name)
        arm = obj1.data
        for obj in bpy.context.selected_objects:
            if obj.type=="ARMATURE" and obj.name != obj1.name:
                obj0=obj
                arm0= obj0.data
                location0=copy.deepcopy(obj0.location)
        
        try:
            bpy.context.scene.cursor.location = Vector((0.0, 0.0, 0.0))
            bpy.context.scene.cursor.rotation_euler = Vector((0.0, 0.0, 0.0))
            with bpy.context.temp_override(selected_editable_objects=bpy.context.selected_objects):
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        except Exception as e: self.report({'INFO'}, f"{e}")
        
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in arm0.edit_bones:
            bone.select = False
            bone.select_head = False
            bone.select_tail = False
        if len(bpy.context.selected_bones)==0:
            parentname = O_attach_Armatures.rreplace(arm0.name, '_m', '', 1)
            if parentname in arm.edit_bones:
                parent = arm.edit_bones[parentname]
            else:
                self.report({'INFO'},f"没选择骨节；没找到{parentname}")
                return {'CANCELLED'}
        else:
            parent = bpy.context.selected_bones[0]
        if parent is None:
            self.report({'INFO'},f"没选择骨节")
            return {'CANCELLED'}
        else:
            self.report({'INFO'},f"父级：{parent.name}")
            
        b1 = arm.edit_bones.new(obj0.name)
        b1.head=parent.head-location0
        b1.tail=b1.head+(parent.tail-parent.head)
        b1.parent=parent
        
        # b2 = arm.edit_bones.new(obj0.name+"_a")
        # b2.head=parent.tail-location0
        # b2.tail=b2.head+(parent.tail-parent.head)
        # b2.parent=parent
        
        parent=b1
        
        for b_orig in arm0.edit_bones:
            self.report({'INFO'},f"createing {b_orig.name}")
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if b_orig.parent is None:
                b.parent = parent
            else:
                b.parent = arm.edit_bones[b_orig.parent.name]
            
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_attach_Armatures2 finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_compare_Armatures(bpy.types.Operator):
    bl_idname = "fdktools.compare_arms"
    bl_label = "对比骨架"
    bl_description = "比较所选骨架，获得差异的骨骼名称"
    
    def execute(self, context):
        bones0=[]
        bones=[]
        result=""
        bpy.context.window_manager.clipboard=""
        arm = bpy.data.objects.get(bpy.context.active_object.name).data
        arm0=None
        for obj in bpy.context.selected_objects:
            if obj.type=="ARMATURE" and obj.name != bpy.context.active_object.name:
                arm0=obj.data
        if arm0 is None:
            self.report({'ERROR'}, "没有选择对象骨架")
            return {'FINISHED'}
        for bone in arm0.bones:
            if not bone.name in arm.bones:
                bones0.append(bone.name)
        for bone in arm.bones:
            if not bone.name in arm0.bones:
                bones.append(bone.name)
        
        result+=f"{arm0.name}：\n    "
        if len(bones0)==0:
            result+="（无）\n"
        else:
            delimiter = "\n    "
            result+=delimiter.join(bones0)
        
        result+=f"{arm.name}：\n    "
        if len(bones)==0:
            result+="（无）\n"
        else:
            delimiter = "\n    "
            result+=delimiter.join(bones)
            
        self.report({'INFO'},result)
        bpy.context.window_manager.clipboard=result
        self.report({'INFO'},f"O_compare_Armatures finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_get_Names_By_Armature(bpy.types.Operator):
    bl_idname = "fdktools.get_name_by_arm"
    bl_label = "获得名称"
    bl_description = "获得无对应骨骼的顶点组名称"
    
    def execute(self, context):
        bpy.context.window_manager.clipboard=""
        bones=[]
        meshes = []
        result= []
        if bpy.context.active_object.type == 'MESH':
            meshes.append(bpy.data.objects.get(bpy.context.active_object.name))
            baseobj = bpy.context.active_object.parent
        else:
            baseobj = bpy.context.active_object
            for obj in bpy.data.objects:
                if obj.type=="MESH" and (not obj.parent is None) and obj.parent.name == baseobj.name:
                    meshes.append(obj)

        arm = bpy.data.objects.get(baseobj.name).data
        for bone in arm.bones:
            bones.append(bone.name)
        for mesh in meshes:
            for vg in mesh.vertex_groups:
                if not vg.name in bones:
                    result.append(f"{mesh.name} : {vg.name}")
        
        if len(result)==0:
            bpy.context.window_manager.clipboard="（无）"
        else:
            delimiter = "\n"
            self.report({'INFO'},delimiter.join(result))
            bpy.context.window_manager.clipboard=delimiter.join(result)
        self.report({'INFO'},f"O_get_Names_By_Armature finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_select_Meshes_By_Armature(bpy.types.Operator):
    bl_idname = "fdktools.select_meshes_by_arm"
    bl_label = "选中"
    bl_description = "根据父级骨骼对指定到顶点组中的顶点进行选中"
    
    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey == '':
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        bones=[]
        meshes = []
        if bpy.context.active_object.type == 'MESH':
            baseobj = bpy.context.active_object.parent
        else:
            baseobj = bpy.context.active_object
        arm = bpy.data.objects.get(baseobj.name).data

        bpy.context.view_layer.objects.active = baseobj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if arm.edit_bones.get(headkey) is not None:
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            for bone in bpy.context.selected_bones:
                bones.append(bone.name)
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in bpy.data.objects:
                if obj.type=="MESH" and (not obj.parent is None) and obj.parent.name == baseobj.name:
                    meshes.append(obj)
            for mesh in meshes:
                vg = mesh.vertex_groups
                hide_state=mesh.hide_get()
                mesh.hide_set(False)
                bpy.context.view_layer.objects.active=mesh
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in bones:
                    if vg.get(bone) is not None:
                        vg_idx = vg[bone].index
                        bpy.data.objects.get(bpy.context.active_object.name).vertex_groups.active_index = vg_idx
                        bpy.ops.object.vertex_group_select()
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh.hide_set(hide_state)
            bpy.context.view_layer.objects.active = baseobj
        else:
            self.report({'INFO'}, f"所选骨架中不存在{headkey}")
            return {'FINISHED'}
        self.report({'INFO'},f"O_select_Meshes_By_Armature finished")
        return {'FINISHED'}
class O_unselect_Meshes_By_Armature(bpy.types.Operator):
    bl_idname = "fdktools.unselect_meshes_by_arm"
    bl_label = "取消选中"
    bl_description = "根据父级骨骼对指定到顶点组中的顶点取消选中"
    
    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey == '':
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        bones=[]
        meshes = []
        if bpy.context.active_object.type == 'MESH':
            baseobj = bpy.context.active_object.parent
        else:
            baseobj = bpy.context.active_object
        arm = bpy.data.objects.get(baseobj.name).data

        bpy.context.view_layer.objects.active = baseobj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if arm.edit_bones.get(headkey) is not None:
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            for bone in bpy.context.selected_bones:
                bones.append(bone.name)
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in bpy.data.objects:
                if obj.type=="MESH" and (not obj.parent is None) and obj.parent.name == baseobj.name:
                    meshes.append(obj)
            for mesh in meshes:
                vg = mesh.vertex_groups
                hide_state=mesh.hide_get()
                mesh.hide_set(False)
                bpy.context.view_layer.objects.active=mesh
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in bones:
                    if vg.get(bone) is not None:
                        vg_idx = vg[bone].index
                        bpy.data.objects.get(bpy.context.active_object.name).vertex_groups.active_index = vg_idx
                        bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh.hide_set(hide_state)
            bpy.context.view_layer.objects.active = baseobj
        else:
            self.report({'INFO'}, f"所选骨架中不存在{headkey}")
            return {'FINISHED'}
        self.report({'INFO'},f"O_unselect_Meshes_By_Armature finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_join_Meshes(bpy.types.Operator):
    bl_idname = "fdktools.join_selected_meshes"
    bl_label = "JOIN & DELETE"
    bl_description = "先选新的，再选旧的，然后JOIN。只有选择2个网格时才有效果。会重置选区。"
    
    def execute(self, context):
        mesh = bpy.data.objects.get(bpy.context.active_object.name)
        mesh0=None
        for obj in bpy.context.selected_objects:
            if obj.type=="MESH" and obj.name != bpy.context.active_object.name:
                mesh0=obj
        if mesh0 is None:
            self.report({'ERROR'}, "没有选择对象网格")
            return {'FINISHED'}

        mesh0.select_set(False)
        mesh.select_set(False)
        bpy.context.view_layer.objects.active=mesh0
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active=mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh0.select_set(True)
        mesh.select_set(True)
        bpy.context.view_layer.objects.active=mesh
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        # context.scene.fdk_source_mesh=None
        # context.scene.fdk_target_mesh=None
        self.report({'INFO'},f"O_join_Meshes finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_renameMaterial(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.rename_material_png"
    bl_label = "贴图后缀名改成png"
    bl_description = "贴图后缀名改成png并重选来源文件夹"
    
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
        # ref:https://blender.stackexchange.com/questions/331452/change-fbx-model-texture-path-to-read-png-instead-of-jpg-texture-images/331460#331460
        for img in bpy.data.images:
            if img.source == 'FILE' and not img.is_dirty and not img.library:
                imgpath = os.path.basename(img.filepath_raw)
                img.filepath_raw = f"{os.path.splitext(imgpath)[0]}.png"
        # 指定查找丢失数据的路径
        # self.report({'INFO'},f"{self.directory}")
        directory = self.directory
        # 查找丢失数据
        bpy.ops.file.find_missing_files(directory=directory)
        # 自动打开文件
        # bpy.ops.file.find_missing_files(open=True)
        remapped_imgs = []
        for img in bpy.data.images:
            if img.source == 'FILE' and not img.is_dirty and not img.library:
                if os.path.exists(os.path.abspath(bpy.path.abspath(img.filepath_raw))):
                    remapped_imgs.append(img)
        for mat in bpy.data.materials:
            if mat.node_tree:
                pbr_nodes = [
                    node for node in mat.node_tree.nodes
                    if node.type == 'BSDF_PRINCIPLED'
                ]
                if len(pbr_nodes) == 1:
                    img_nodes = [
                        node for node in mat.node_tree.nodes
                        if node.type == 'TEX_IMAGE' and node.image and node.image in remapped_imgs
                    ]
                    for img_node in img_nodes:
                        if not img_node.outputs['Alpha'].is_linked:
                            mat.node_tree.links.new(img_node.outputs['Alpha'], pbr_nodes[0].inputs['Alpha'])
        self.report({'INFO'},f"rename_material_png finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_renameMaterialdds(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.rename_material_dds"
    bl_label = "贴图后缀名改成dds"
    bl_description = "贴图后缀名改成dds并重选来源文件夹"
    
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
        # ref:https://blender.stackexchange.com/questions/331452/change-fbx-model-texture-path-to-read-png-instead-of-jpg-texture-images/331460#331460
        for img in bpy.data.images:
            if img.source == 'FILE' and not img.is_dirty and not img.library:
                imgpath = os.path.basename(img.filepath_raw)
                img.filepath_raw = f"{os.path.splitext(imgpath)[0]}.dds"
        # 指定查找丢失数据的路径
        # self.report({'INFO'},f"{self.directory}")
        directory = self.directory
        # 查找丢失数据
        bpy.ops.file.find_missing_files(directory=directory)
        # 自动打开文件
        # bpy.ops.file.find_missing_files(open=True)
        remapped_imgs = []
        for img in bpy.data.images:
            if img.source == 'FILE' and not img.is_dirty and not img.library:
                if os.path.exists(os.path.abspath(bpy.path.abspath(img.filepath_raw))):
                    remapped_imgs.append(img)
        for mat in bpy.data.materials:
            if mat.node_tree:
                pbr_nodes = [
                    node for node in mat.node_tree.nodes
                    if node.type == 'BSDF_PRINCIPLED'
                ]
                if len(pbr_nodes) == 1:
                    img_nodes = [
                        node for node in mat.node_tree.nodes
                        if node.type == 'TEX_IMAGE' and node.image and node.image in remapped_imgs
                    ]
                    for img_node in img_nodes:
                        if not img_node.outputs['Alpha'].is_linked:
                            mat.node_tree.links.new(img_node.outputs['Alpha'], pbr_nodes[0].inputs['Alpha'])
        self.report({'INFO'},f"rename_material_dds finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_get_MaterialName(bpy.types.Operator):
    bl_idname = "fdktools.get_material_images"
    bl_label = "复制贴图参数"
    bl_description = "复制所选网格或骨架的材质和贴图名到剪贴板"
    
    def execute(self, context):
        objs=[]
        bpy.context.window_manager.clipboard=""
        if bpy.context.active_object.type=="MESH":
            objs.append(bpy.context.active_object)
        elif bpy.context.active_object.type=="ARMATURE":
            for child in bpy.context.active_object.children:
                if child.type=="MESH":
                    objs.append(child)
        else:
            self.report({'INFO'},f"必须选择骨架或者网格")
            return {'CANCELLED'}
        result=[]
        for obj in objs:
            # mesh = obj.data
            for slot in obj.material_slots:
                mat = slot.material
                if mat is not None:
                    result.append(""+mat.name)
                    for node in mat.node_tree.nodes:
                        for slot_base_color in node.inputs:
                            if slot_base_color.type == "RGBA" and slot_base_color.is_linked:
                                node_base_color = slot_base_color.links[0].from_node
                                if node_base_color.type == "MIX":
                                    for slot_base_color2 in node_base_color.inputs:
                                        if slot_base_color2.is_linked:
                                            node_base_color2 = slot_base_color2.links[0].from_node
                                            if node_base_color2.type == 'TEX_IMAGE':
                                                result.append('    '+node_base_color2.image.name)
                                elif not node_base_color.type == "VERTEX_COLOR":
                                    try:
                                        result.append('    '+node_base_color.image.name)
                                    except:
                                        self.report({'ERROR'},f"    exception:{node_base_color.type}")

        delimiter = "\n"
        self.report({'INFO'},delimiter.join(result))
        bpy.context.window_manager.clipboard=delimiter.join(result)
        self.report({'INFO'},f"O_get_MaterialName finished")
        return {'FINISHED'}
########################## Divider ##########################   
class FDK_PT_Snippets(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets"
    bl_label = "全局配置"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'

    @classmethod
    def poll(cls, context):
        return True #context.scene.active_fdktools_subpanel == 'BoneTools'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        # col.label(text="全局配置")
        if context.scene.fdk_config_json_data:
            col.operator(O_ImportJSON.bl_idname, icon="IMPORT", text="重选配置JSON")#导入配置JSON
        else:
            col.operator(O_ImportJSON.bl_idname, icon="IMPORT")#导入配置JSON
        # col.operator(O_AssignArmature.bl_idname, text=O_AssignArmature.bl_label, icon="ARMATURE_DATA")
        
        # col.prop(context.scene, "fdk_target_armature", text="目标骨架", icon="ARMATURE_DATA")
        row = col.row(align=True)
        row.label(text="目标骨架：",icon="ARMATURE_DATA")
        if bpy.context.active_object and bpy.context.active_object.type=="ARMATURE":
            row.label(text=bpy.context.active_object.name)
        else:
            row.label(text="（未选择）")
        
        sel_obj=None
        if len(bpy.context.selected_objects)>0:
            for obj in bpy.context.selected_objects:
                if obj.type=="ARMATURE" and obj.name != bpy.context.active_object.name:
                    sel_obj=obj

        row = col.row(align=True)
        row.label(text="源骨架：",icon="ARMATURE_DATA")
        if sel_obj is None:
            row.label(text="（未选择）")
        else:
            row.label(text=sel_obj.name)
        O_CopyBonecol = box.column(align=True)
        O_CopyBonecol.operator(O_CopyBone.bl_idname, text=O_CopyBone.bl_label, icon="ARMATURE_DATA")#复制位置
                
        if (not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")) or (sel_obj is None):
            O_CopyBonecol.enabled=False
            col = box.column(align=True)
            col.label(text="先选择骨架才能操作")
        elif not context.scene.fdk_config_json_data:
            O_CopyBonecol.enabled=False
            col = box.column(align=True)
            col.label(text="先导入JSON才能操作")
        # row = O_CopyBonecol.row(align=True)
        # row.prop(context.scene, "change_matrix", text="copy_matrix")
        # row.prop(context.scene, "change_tail", text="copy_tail")
        # row.prop(context.scene, "reset_empty", text="reset_empty")
        
        # if context.scene.fdk_config_json_data:
            # col.prop(context.scene, "fdk_source_armature", text="源骨架", icon="ARMATURE_DATA")
            # if context.scene.fdk_source_armature:
                # col.operator(O_CopyBone.bl_idname, text=O_CopyBone.bl_label, icon="BONE_DATA")#复制位置
            # else:
                # col.label(text="先选择源骨架才能复制位置")
        # else:
            # box = layout.box()
            # col = box.column()
            # col.label(text="先导入JSON才能复制位置")
        col = box.column(align=True)
        O_CopyBonerow = col.row(align=True)
        O_CopyBonerow.operator(O_compare_Armatures.bl_idname, text=O_compare_Armatures.bl_label, icon="COPYDOWN")#对比骨架
        O_CopyBonerow.operator(O_copy_Armatures.bl_idname, text=O_copy_Armatures.bl_label, icon="COPYDOWN")#复制结构

class FDK_PT_Snippets_Target(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_Target"
    bl_label = "编辑目标骨架"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'

    @classmethod
    def poll(cls, context):
        return True#context.scene.fdk_target_armature
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        
        if not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE"):
            box.enabled=False
            col.label(text="先选择目标骨架才能操作")
        else:
            col.label(text="与指定父级骨骼相关操作")
            
        col.prop(context.scene, 'fdk_modify_headname',icon="BONE_DATA")
        child_row = col.row(align=True)
        if context.scene.fdk_modify_headname == "":
            child_row.enabled = False
        child_row.operator(O_DelBone.bl_idname, text=O_DelBone.bl_label, icon="BONE_DATA")#删除子级
        child_row.operator(O_DelOtherBone.bl_idname, text=O_DelOtherBone.bl_label, icon="BONE_DATA")#删除其他
        child_row = col.row(align=True)
        if context.scene.fdk_modify_headname == "":
            child_row.enabled = False
        child_row.operator(O_select_Meshes_By_Armature.bl_idname, text=O_select_Meshes_By_Armature.bl_label, icon="MESH_DATA")#选取顶点
        child_row.operator(O_unselect_Meshes_By_Armature.bl_idname, text=O_unselect_Meshes_By_Armature.bl_label, icon="MESH_DATA")#取消顶点
        
        if context.scene.fdk_config_json_data:
            # col.label(text="Hint:父级为空则只按json复制指定子级，不会重命名其他")
            # row.prop(context.scene, 'fdk_rename_copy_prefix')
            row = col.row(align=True)
            if context.scene.fdk_modify_headname == "":
                row.prop(context.scene, 'fdk_rename_orig_prefix')
                col.operator(O_RenameBone.bl_idname, text="复制指定子级", icon="BONE_DATA")#重命名子级
            else:
                # row.prop(context.scene, 'fdk_rename_orig_prefix')
                row.prop(context.scene, 'fdk_rename_prefix')
                col.operator(O_RenameBone.bl_idname, text="重命名及复制指定子级", icon="BONE_DATA")#重命名子级
            col.operator(O_AddEmpty.bl_idname, text=O_AddEmpty.bl_label, icon="EMPTY_DATA")#添加空物体
        else:
            col.operator(O_ImportJSON.bl_idname, icon="IMPORT", text="脸部改名/添加空物体需先选择配置JSON")
            
        box = layout.box()
        col = box.column(align=True)
        col.label(text="依照replace_dict.json重命名目标骨架")
        if not context.scene.fdk_rename_pair_json_data:
            col.operator(O_ImportRenameJSON.bl_idname, icon="IMPORT")#重命名配对JSON
        else:
            col.operator(O_ImportRenameJSON.bl_idname, icon="IMPORT", text="重选配对JSON")
            
        O_RenameByJSONcol = box.column(align=True)
        if (not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")) or (not context.scene.fdk_rename_pair_json_data):
            O_RenameByJSONcol.enabled = False
        O_RenameByJSONcol.operator(O_RenameByJSON.bl_idname, text=O_RenameByJSON.bl_label, icon="BONE_DATA")

class FDK_PT_Snippets_FGOA(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_FGOA"
    bl_label = "FGOA用"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    bl_options = {'DEFAULT_CLOSED'} #默认折叠
    
    @classmethod
    def poll(cls, context):
        return True #context.scene.active_fdktools_subpanel == 'BoneTools'
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        col = box.column(align=True)
        
        sel_obj=None
        if bpy.context.active_object and bpy.context.active_object.type=="MESH":
            if len(bpy.context.selected_objects)>0:
                for obj in bpy.context.selected_objects:
                    if obj.type=="MESH" and obj.name != bpy.context.active_object.name:
                        sel_obj=obj
                if sel_obj:
                    row = col.row(align=True)
                    row.label(text="源网格：")
                    row.label(text=sel_obj.name)
                else:
                    col.label(text="选择源网格才能合并")
        
        O_CopyBonerow = col.row(align=True)
        O_CopyBonerow.operator(O_attach_Armatures.bl_idname, text=O_attach_Armatures.bl_label, icon="ARMATURE_DATA")
        O_CopyBonerow.operator(O_attach_Armatures2.bl_idname, text=O_attach_Armatures2.bl_label, icon="ARMATURE_DATA")
        col.enabled = (not sel_obj is None) and (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")
        
        child_row = col.row(align=True)
        if (bpy.context.object is None) or (not (bpy.context.object.mode == 'EDIT' and bpy.context.selected_editable_bones != None and len(bpy.context.selected_editable_bones) ==2)):
            child_row.enabled = False
        child_row.operator(O_copy_Bone_Pos.bl_idname, text=O_copy_Bone_Pos.bl_label, icon="COPYDOWN")
        child_row.operator(O_copy_Bone_Pos2.bl_idname, text=O_copy_Bone_Pos2.bl_label, icon="COPYDOWN")
        child_row.operator(O_copy_Bone_Pos3.bl_idname, text=O_copy_Bone_Pos3.bl_label, icon="COPYDOWN")
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="依照json重组目标骨架")
        if not context.scene.fdk_moving_pair_json_data:
            col.operator(O_ImportMovingJSON.bl_idname, icon="IMPORT")#重命名配对JSON
        else:
            col.operator(O_ImportMovingJSON.bl_idname, icon="IMPORT", text="重选配对JSON")
        O_RenameByJSONcol = box.column(align=True)
        if (not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")) or (not context.scene.fdk_moving_pair_json_data):
            O_RenameByJSONcol.enabled = False
        O_RenameByJSONcol.operator(O_MoveByJSON.bl_idname, text=O_MoveByJSON.bl_label, icon="BONE_DATA")
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(O_renameMaterial.bl_idname, text=O_renameMaterial.bl_label)
        row.operator(O_renameMaterialdds.bl_idname, text=O_renameMaterialdds.bl_label)

class FDK_PT_Snippets_Others(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_Others"
    bl_label = "其他快捷操作"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    
    @classmethod
    def poll(cls, context):
        return True #context.scene.active_fdktools_subpanel == 'BoneTools'
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.operator(O_del_glTF_not.bl_idname, text=O_del_glTF_not.bl_label, icon="EMPTY_DATA")
        row = col.row(align=True)
        row.operator(O_hideEmpty.bl_idname, text=O_hideEmpty.bl_label, icon="EMPTY_DATA")
        row.operator(O_showEmpty.bl_idname, text=O_showEmpty.bl_label, icon="EMPTY_DATA")
        row.operator(O_delEmpty.bl_idname, text=O_delEmpty.bl_label, icon="EMPTY_DATA")
        
        child_row = col.row(align=True)
        if not (bpy.context.active_object and bpy.context.active_object.type=="EMPTY"):
            child_row.enabled = False
        child_row.operator(O_resetEmptyRot1.bl_idname, text=O_resetEmptyRot1.bl_label, icon="EMPTY_DATA")
        child_row.operator(O_resetEmptyRot2.bl_idname, text=O_resetEmptyRot2.bl_label, icon="EMPTY_DATA")
        child_row.operator(O_copyEmptyRot.bl_idname, text=O_copyEmptyRot.bl_label, icon="EMPTY_DATA")
        
        child_row = col.row(align=True)
        if not (bpy.context.active_object and (bpy.context.active_object.type=="MESH" or bpy.context.active_object.type=="ARMATURE")):
            child_row.enabled = False
        child_row.operator(O_remove_Empty_Bone.bl_idname, text=O_remove_Empty_Bone.bl_label, icon="BONE_DATA")
        child_row.operator(O_get_Names_By_Armature.bl_idname, text=O_get_Names_By_Armature.bl_label, icon="COPYDOWN")

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="目标网格：")
        if bpy.context.active_object and bpy.context.active_object.type=="MESH":
            row.label(text=bpy.context.active_object.name)
        else:
            row.label(text="（未选择）")
            col.label(text="选择网格才能操作")
            
        sel_obj=None
        if bpy.context.active_object and bpy.context.active_object.type=="MESH":
            if len(bpy.context.selected_objects)>0:
                for obj in bpy.context.selected_objects:
                    if obj.type=="MESH" and obj.name != bpy.context.active_object.name:
                        sel_obj=obj
                if sel_obj:
                    row = col.row(align=True)
                    row.label(text="源网格：")
                    row.label(text=sel_obj.name)
                else:
                    col.label(text="选择源网格才能合并")
        col = box.column(align=True)
        col.operator(O_join_Meshes.bl_idname, text=O_join_Meshes.bl_label, icon="MESH_DATA")
        if (sel_obj is None) or (not (bpy.context.active_object and bpy.context.active_object.type=="MESH")):
            col.enabled=False
            
        box = layout.box()
        col = box.column(align=True)
        col.label(text="选择骨架或网格复制贴图到剪贴板")
        O_get_MaterialNamecol = box.column(align=True)
        if not (bpy.context.active_object and (bpy.context.active_object.type=="MESH" or bpy.context.active_object.type=="ARMATURE")):
            O_get_MaterialNamecol.enabled=False
        O_get_MaterialNamecol.operator(O_get_MaterialName.bl_idname, text=O_get_MaterialName.bl_label,icon="COPYDOWN")

class FDK_PT_Snippets_IO(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_IO"
    bl_label = "I/O"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    
    @classmethod
    def poll(cls, context):
        return True #context.scene.active_fdktools_subpanel == 'BoneTools'
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, "compare_local", text="本地数据💡")
        row = col.row(align=True)
        row.operator(O_ImportMDL.bl_idname, icon="IMPORT")#Import MDL
        row.prop(context.scene, "usedds", text="使用dds贴图")
        col.operator(O_ExportVBIB.bl_idname, icon="EXPORT")#Export VBIB
        row = col.row(align=True)
        row.operator(O_ExportMDLJson.bl_idname, icon="TRACKING_FORWARDS")#MDL export JSON
        row.operator(O_ExportMDLMetadata.bl_idname, icon="TRACKING_FORWARDS")#MDL export metadata
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(O_UpdateMDL.bl_idname, icon="TRACKING_BACKWARDS")#Import VBIB to MDL
        row.prop(context.scene, "do_not_backup", text="不创建bak")
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        if bpy.context.scene.compare_local == True:
            row.operator(O_CheckMaterialsLocal.bl_idname, icon="MATERIAL")#Compare Material JSON
        else:
            row.operator(O_CheckMaterials.bl_idname, icon="MATERIAL")#Compare Material JSON
        box = layout.box()
        col = box.column(align=True)
        # col.prop(context.scene, "fdk_source_mesh", text="源网格", icon="MESH_DATA")
        # col.prop(context.scene, "fdk_target_mesh", text="目标网格", icon="MESH_DATA")
        # col.operator(O_join_Meshes.bl_idname, text=O_join_Meshes.bl_label, icon="MESH_DATA")
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
    #O_AssignArmature,
    O_ImportJSON,
    O_ImportRenameJSON,
    O_ImportMovingJSON,
    O_DelBone,
    O_DelOtherBone,
    O_select_Meshes_By_Armature,
    O_unselect_Meshes_By_Armature,
    O_RenameBone,
    O_CopyBone,
    O_compare_Armatures,
    O_copy_Armatures,
    O_attach_Armatures,
    O_attach_Armatures2,
    O_AddEmpty,
    O_RenameByJSON,
    O_MoveByJSON,
    O_hideEmpty,
    O_showEmpty,
    O_delEmpty,
    O_resetEmptyRot1,
    O_resetEmptyRot2,
    O_copyEmptyRot,
    O_del_glTF_not,
    O_join_Meshes,
    O_get_MaterialName,
    O_get_Names_By_Armature,
    O_copy_Bone_Pos,
    O_copy_Bone_Pos2,
    O_copy_Bone_Pos3,
    O_remove_Empty_Bone,
    O_renameMaterial,
    O_renameMaterialdds,
    FDK_PT_Snippets,
    FDK_PT_Snippets_Target,
    FDK_PT_Snippets_FGOA,
    FDK_PT_Snippets_Others,
    FDK_PT_Snippets_IO,
    HelloWorldPanel
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.my_list = bpy.props.CollectionProperty(type = MaterialListItem)
    bpy.types.Scene.list_index = bpy.props.IntProperty(name = "Index for my_list", default = 0)
    
    bpy.types.Scene.metadata_list = bpy.props.CollectionProperty(type = MetadataListItem)
    bpy.types.Scene.metadata_index = bpy.props.IntProperty(name = "Index for metadata_list", default = 0)
    
    bpy.types.Scene.fdk_config_json_data = bpy.props.StringProperty(
        name="Config JSON Data",description="配置数据",default=""
    )
    bpy.types.Scene.fdk_rename_pair_json_data = bpy.props.StringProperty(
        name="Rename JSON Data",description="重命名配对数据",default=""
    )
    bpy.types.Scene.fdk_moving_pair_json_data = bpy.props.StringProperty(
        name="Rename JSON Data",description="重组配对数据",default=""
    )
    # bpy.types.Scene.fdk_source_armature = bpy.props.PointerProperty(
        # description="选择一个骨架作为数据源",type=bpy.types.Object,poll=ObjType.is_armature
    # )
    # bpy.types.Scene.fdk_target_armature = bpy.props.PointerProperty(
        # description="选择将被作用的骨架",type=bpy.types.Object,poll=ObjType.is_armature
    # )
    bpy.types.Scene.fdk_modify_headname = bpy.props.StringProperty(
        name="父级",description="设置父级名字",default= "Head"
    )
    bpy.types.Scene.fdk_rename_prefix = bpy.props.StringProperty(
        name="改名规则",description="设置要改成新名字时，要添加的后缀字符",default= "_New"
    )
    # bpy.types.Scene.fdk_rename_copy_prefix = bpy.props.StringProperty(
        # name="备份",description="设置要添加到备份的后缀字符",default= "_Copy"
    # )
    bpy.types.Scene.fdk_rename_orig_prefix = bpy.props.StringProperty(
        name="原骨骼改名规则",description="用于空re调整眼睛特写高度，将复制骨骼并按后缀重命名原骨骼",default= "_Orig"
    )
    # bpy.types.Scene.fdk_source_mesh = bpy.props.PointerProperty(
        # description="选择一个网格作为数据源",type=bpy.types.Object,poll=ObjType.is_mesh
    # )
    # bpy.types.Scene.fdk_target_mesh = bpy.props.PointerProperty(
        # description="选择将被作用的网格",type=bpy.types.Object,poll=ObjType.is_mesh
    # )
    bpy.types.Scene.change_matrix = bpy.props.BoolProperty(
        name="copy matrix",description="(实验功能)",default= False
    )
    bpy.types.Scene.change_tail = bpy.props.BoolProperty(
        name="copy tail",description="(实验功能)",default= True
    )
    bpy.types.Scene.reset_empty = bpy.props.BoolProperty(
        name="reset empty",description="(实验功能)",default= True
    )
    bpy.types.Scene.do_not_backup = bpy.props.BoolProperty(
        name="donot backup",description="导入时不创建bak",default= True
    )
    bpy.types.Scene.compare_local = bpy.props.BoolProperty(
        name="compare local",description="使用从mdl导入内部的数据。只对带💡的项目有效。",default= True
    )
    bpy.types.Scene.usedds = bpy.props.BoolProperty(
        name="use dds",description="改用dds",default= True
    )

def unregister():
    del bpy.types.Scene.my_list
    del bpy.types.Scene.list_index
    del bpy.types.Scene.metadata_list
    del bpy.types.Scene.metadata_index
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.fdk_config_json_data
    del bpy.types.Scene.fdk_rename_pair_json_data
    del bpy.types.Scene.fdk_moving_pair_json_data
    # del bpy.types.Scene.fdk_source_armature
    # del bpy.types.Scene.fdk_target_armature
    # del bpy.types.Scene.fdk_source_mesh
    # del bpy.types.Scene.fdk_target_mesh
    del bpy.types.Scene.fdk_modify_headname
    del bpy.types.Scene.fdk_rename_prefix
    # del bpy.types.Scene.fdk_rename_copy_prefix
    del bpy.types.Scene.fdk_rename_orig_prefix
    
    del bpy.types.Scene.change_matrix
    del bpy.types.Scene.change_tail
    del bpy.types.Scene.reset_empty
    del bpy.types.Scene.do_not_backup
    del bpy.types.Scene.compare_local
    del bpy.types.Scene.usedds