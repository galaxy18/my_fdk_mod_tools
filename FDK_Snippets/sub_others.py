try:
    import bpy,os,json,shutil,mathutils,math,numpy,copy
    from bpy_extras.io_utils import ImportHelper, ExportHelper
    from mathutils import Vector
except ModuleNotFoundError as e:
    print("Python module missing! {}".format(e.msg))
    input("Press Enter to abort.")
    raise
########################## Divider ##########################
class FDK_PT_Snippets_FGOA(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_FGOA"
    bl_label = "FGOA用"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    #bl_options = {'DEFAULT_CLOSED'} #默认折叠
    
    @classmethod
    def poll(cls, context):
        return context.scene.active_xbone_subpanel == 'Others'
    
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
        if (not "fdk_moving_pair_json_data" in context.scene):
            col.operator(O_ImportMovingJSON.bl_idname, icon="IMPORT")#重命名配对JSON
        else:
            col.operator(O_ImportMovingJSON.bl_idname, icon="IMPORT", text="重选配对JSON")
        O_RenameByJSONcol = box.column(align=True)
        if (not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")) or (not "fdk_moving_pair_json_data" in context.scene):
            O_RenameByJSONcol.enabled = False
        O_RenameByJSONcol.operator(O_MoveByJSON.bl_idname, text=O_MoveByJSON.bl_label, icon="BONE_DATA")
########################## Divider ##########################
########################## Divider ##########################
class O_attach_Armatures(bpy.types.Operator):
    bl_idname = "fdktools.attach_bones"
    bl_label = "Attach"
    bl_description = "添加到选中骨骼做子级"
    bl_options = {'UNDO'}
    
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
    bl_options = {'UNDO'}
    
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
class O_copy_Bone_Pos(bpy.types.Operator):
    bl_idname = "fdktools.copy_bonepos"
    bl_label = "复制骨节位置"
    bl_description = "在编辑模式选中两段骨节复制位置"
    bl_options = {'UNDO'}
    
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
    bl_options = {'UNDO'}
    
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
    bl_options = {'UNDO'}
    
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
class O_ImportMovingJSON(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.json_moving_import"
    bl_label = "选择重组配置JSON"
    bl_description = "导入窗口右上角选择编码格式"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_options = {'UNDO'}
    
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
class O_MoveByJSON(bpy.types.Operator):
    bl_idname = "fdktools.move_by_json"
    bl_label = "根据JSON重组"
    bl_description = "根据JSON修改目标骨架父子级关系"
    bl_options = {'UNDO'}
    
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

########################## Divider ##########################
class FDK_PT_Snippets_YS9(bpy.types.Panel):
    bl_idname = "FDK_PT_Snippets_YS9"
    bl_label = "YS9用"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FDK_Snippets'
    #bl_options = {'DEFAULT_CLOSED'} #默认折叠
    
    @classmethod
    def poll(cls, context):
        return context.scene.active_xbone_subpanel == 'Others'
        
    def draw(self, context):
        from . import panel
        layout = self.layout
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="注意：会影响全部网格")
        
        col = box.column(align=True)
        col.operator(panel.O_del_glTF_not.bl_idname)
        col.operator(panel.O_delEmpty.bl_idname)
        col.operator(O_removeArmatures.bl_idname)#移除骨架
        col.operator(O_removeAlphaLink.bl_idname)#断开Alpha
        col.operator(O_removeBackfaceCulling.bl_idname)#背面剔除
        col.label(text="背面剔除体积光照探头")
        row = col.row()
        row.operator(O_removeBackfaceCullingLight.bl_idname)#背面剔除
        row.operator(O_recoverBackfaceCullingLight.bl_idname)#背面剔除
        
        col = box.column(align=True)
        col.label(text="对选中的网格进行位移")
        col.operator(O_moveObjects.bl_idname)#將xy坐标移动到邊界框中心
        col.operator(O_moveObjectsZ.bl_idname)#按活动物体设定z坐标
        
        col = box.column(align=True)
        col.operator(O_removeVERTEXCOLOR.bl_idname)
########################## Divider ##########################
class O_removeAlphaLink(bpy.types.Operator):
    bl_idname = "fdktools.remove_alpha_links"
    bl_label = "断开Alpha"
    bl_description = "断开Alpha"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        # import bpy
        # from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
        for mat in bpy.data.materials:
            mat.blend_method = 'OPAQUE'
            if mat.node_tree is None:
                continue
            nodes = mat.node_tree.nodes
            for node in nodes:
                # print(node.bl_idname)
                if node.bl_idname == "ShaderNodeBsdfPrincipled":
                    # print(len(node.inputs["Alpha"].links))
                    node.inputs["Alpha"].default_value = 1
                    for link in node.inputs["Alpha"].links:
                        mat.node_tree.links.remove(link)
        return {'FINISHED'}
                        
class O_removeBackfaceCulling(bpy.types.Operator):
    bl_idname = "fdktools.remove_backface_culling"
    bl_label = "移除背面剔除"
    bl_description = "因为游戏的sample里保留了体积光照探头，这里也作保留"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for mat in bpy.data.materials:
            mat.use_backface_culling = False
            mat.use_backface_culling_shadow = False
            # mat.use_backface_culling_lightprobe_volume = True
        return {'FINISHED'}

class O_removeArmatures(bpy.types.Operator):
    bl_idname = "fdktools.remove_armatures"
    bl_label = "移除骨架"
    bl_description = "移除骨架"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type=="ARMATURE":
                bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}
        
class O_removeBackfaceCullingLight(bpy.types.Operator):
    bl_idname = "fdktools.remove_backface_culling_light"
    bl_label = "全部OFF"
    bl_description = ""
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for mat in bpy.data.materials:
            mat.use_backface_culling_lightprobe_volume = False
        return {'FINISHED'}
        
class O_recoverBackfaceCullingLight(bpy.types.Operator):
    bl_idname = "fdktools.recover_backface_culling_light"
    bl_label = "全部ON"
    bl_description = ""
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for mat in bpy.data.materials:
            mat.use_backface_culling_lightprobe_volume = True
        return {'FINISHED'}
        
class O_removeVERTEXCOLOR(bpy.types.Operator):
    bl_idname = "fdktools.remove_vertexcolor"
    bl_label = "移除ShaderNodeVertexColor"
    bl_description = ""
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for mat in bpy.data.materials:
            if not mat.node_tree:
                continue
            nodes_to_remove = [node for node in mat.node_tree.nodes if node.type == 'VERTEX_COLOR']
            for node in nodes_to_remove:
                mat.node_tree.nodes.remove(node)
        return {'FINISHED'}

class O_moveObjects(bpy.types.Operator):
    bl_idname = "fdktools.move_objects"
    bl_label = "边界框中心移动到坐标原点"
    bl_description = ""
    bl_options = {'UNDO'}
    
    def execute(self, context):
        if len(bpy.context.selected_objects)==0:
            return {'CANCELLED'}
        selected_objects = bpy.context.selected_objects
        bbox_center = sum((obj.matrix_world @ Vector(b) for obj in selected_objects for b in obj.bound_box), Vector()) / (8 * len(selected_objects))
        bbox_center.z=0
        for obj in selected_objects:
            obj.location = obj.location-bbox_center
            #mb = obj.matrix_basis
            #obj.data.transform(mb)
            #obj.matrix_basis.identity()
        return {'FINISHED'}
        
class O_moveObjectsZ(bpy.types.Operator):
    bl_idname = "fdktools.move_objectsz"
    bl_label = "按活动物体底边对齐到坐标轴"
    bl_description = ""
    bl_options = {'UNDO'}
    
    def execute(self, context):
        if len(bpy.context.selected_objects)==0:
            return {'CANCELLED'}
        if (bpy.context.active_object is None) or (not bpy.context.active_object.type=="MESH"):
            return {'CANCELLED'}
        selected_objects = bpy.context.selected_objects
        active_obj = bpy.context.active_object
        bbox_world = [active_obj.matrix_world @ Vector(corner) for corner in active_obj.bound_box]
        min_z = min(v.z for v in bbox_world)
        offset = Vector([0,0,min_z])
        for obj in selected_objects:
            obj.location = obj.location-offset
            #mb = obj.matrix_basis
            #obj.data.transform(mb)
            #obj.matrix_basis.identity()
        return {'FINISHED'}
########################## Divider ##########################
classes = [
    FDK_PT_Snippets_FGOA,
    O_attach_Armatures,
    O_attach_Armatures2,
    O_copy_Bone_Pos,
    O_copy_Bone_Pos2,
    O_copy_Bone_Pos3,
    O_ImportMovingJSON,
    O_MoveByJSON,
    FDK_PT_Snippets_YS9,
    O_removeAlphaLink,
    O_removeBackfaceCulling,
    O_removeBackfaceCullingLight,
    O_recoverBackfaceCullingLight,
    O_removeArmatures,
    O_moveObjects,
    O_moveObjectsZ,
    O_removeVERTEXCOLOR
]
########################## Divider ##########################
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.fdk_moving_pair_json_data = bpy.props.StringProperty(
        name="Rename JSON Data",description="重组配对数据",default=""
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.fdk_moving_pair_json_data