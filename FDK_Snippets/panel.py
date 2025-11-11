# type: ignore
import bpy,os,json
import mathutils,math,numpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector,Quaternion
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
                warning = ""
                keys = ["CopyBone_arr_base","CopyBone_arr_names",
                    "CopyBone_arr_ignore","CopyBone_arr_add",
                    "CopyBone_arr_add_ignore","AddEmpty_arr_addPoint",
                    "RenameBone_arr_copy","RenameBone_arr_copy_ignore"]
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
                    if "Headkey" in fdk_config_json_data:
                        context.scene.fdk_modify_headname=fdk_config_json_data["Headkey"]
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
    bl_description = "根据所输入父级骨骼名字删除其以外的骨骼"
    
    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey is None or headkey == "":
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.get(context.scene.fdk_target_armature.name).select_set(True)
        bpy.context.view_layer.objects.active=bpy.data.objects.get(context.scene.fdk_target_armature.name)
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
    bl_description = "根据所输入父级骨骼名字删除其所有子骨骼"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if headkey is None or headkey == "":
            self.report({'ERROR'}, "没有headkey") 
            return {'FINISHED'}
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.get(context.scene.fdk_target_armature.name).select_set(True)
        bpy.context.view_layer.objects.active=bpy.data.objects.get(context.scene.fdk_target_armature.name)
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
    #TODO: config prefix
    bl_idname = "fdktools.rename_head_bones"
    bl_label = "重命名脸部顶点组"
    bl_description = "根据所输入父级骨骼名字重命名子级，根据JSON配置复制一份原名骨骼以应对定位"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        self.report({'DEBUG'}, f"O_RenameBone：父级：{headkey}")
        if not "fdk_config_json_data" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            try:
                arr_copy=json.loads(context.scene["fdk_config_json_data"])["RenameBone_arr_copy"]["data"]
                arr_copy_ignore=json.loads(context.scene["fdk_config_json_data"])["RenameBone_arr_copy_ignore"]["data"]
            except:
                self.report({'ERROR'}, "无效的配置JSON；"+
                "请检查RenameBone_arr_copy和RenameBone_arr_copy_ignore。将不会复制定位骨骼")
                arr_copy=[]
                arr_copy_ignore=[]
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.get(context.scene.fdk_target_armature.name).select_set(True)
        bpy.context.view_layer.objects.active=bpy.data.objects.get(context.scene.fdk_target_armature.name)
        bpy.ops.object.mode_set(mode='EDIT')
        newbones=[]
        for bonename in arr_copy:
            bpy.ops.armature.select_all(action='DESELECT')
            try:
                self.report({'INFO'}, "copying "+bonename)
                arm.edit_bones.active = arm.edit_bones[bonename]
                self.report({'INFO'}, bpy.context.selected_editable_bones[0].name)
                b = bpy.context.selected_editable_bones[0]
                cb = arm.edit_bones.new(bonename+"_Copy")
                cb.head = b.head
                cb.tail = b.tail
                cb.matrix = b.matrix
                cb.parent = b.parent
                newbones.append(cb)
                if headkey=="":
                    arm.edit_bones[bonename].name=bonename+"_Orig"
            except Exception as e: _console.report({'INFO'}, e)
        if not headkey=="":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects.get(context.scene.fdk_target_armature.name).select_set(True)
            bpy.context.view_layer.objects.active=bpy.data.objects.get(context.scene.fdk_target_armature.name)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            for obj in bpy.context.selected_editable_bones:
                if not (obj.name in arr_copy_ignore or obj.name.endswith("_Copy") 
                or obj.name.endswith("_New") or obj.name.endswith("_Orig")):
                    oldname = obj.name
                    obj.name = oldname+"_New"
        for obj in newbones:
            obj.name = obj.name.replace("_Copy", "")

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_RenameBone finished")
        return {'FINISHED'}
        
class O_AddEmpty(bpy.types.Operator):
    bl_idname = "fdktools.add_empty_objects"
    bl_label = "添加空物体"
    bl_description = "添加空物体。配置中父级为骨架的将设为目标骨架"
    
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
            try:
                if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                    context.scene.fdk_target_armature = bpy.context.active_object
                parentobj=bpy.data.objects.get(context.scene.fdk_target_armature.name)
                arm = parentobj.data
            except:
                self.report({'ERROR'}, "没有选择目标骨架") 
                return {'FINISHED'}
        
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
                        emptyobj.location = arm.bones[obj[3]].tail
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
    bl_description = "根据JSON配置复制位置"

    def create_Bone(_console, _context, arm0, arm, b_orig):
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
        # _console.report({'INFO'}, '    processing children of'+b_orig.name)
        for obj in bpy.data.objects:
            if obj.parent_type=='BONE' and obj.parent_bone == b_orig.name and obj.type == "EMPTY":
                obj.rotation_quaternion = Quaternion([1,0,0,0])
                obj.scale = [1.0,1.0,1.0]
        for child in b_orig.children:
            # _console.report({'INFO'}, '    child:'+child.name)
            O_CopyBone.create_Bone(_console, _context, arm0, arm, child)

    def create_Parent(arm0, arm, b_orig):
        _console.report({'INFO'}, '        Info: creating parent bone '+b_orig.name+' can not be skipped')
        if arm.edit_bones.get(b_orig.name) is None:
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if arm.edit_bones.get(b_orig.parent.name) is None:
                O_CopyBone.create_Parent(arm0, arm, b_orig.parent)
            b.parent = arm.edit_bones[b_orig.parent.name]

    def processname(_console, _context, arm0, arm, b_child, processchild=True):
        try:
            arr_ignore = json.loads(_context.scene["fdk_config_json_data"])["CopyBone_arr_ignore"]["data"]
        except:
            arr_ignore=[]
        changes=mathutils.Vector((0,0,0))
        try:
            if arm.edit_bones.get(b_child.name) is None:
                O_CopyBone.create_Bone(_console, _context, arm0, arm, b_child)
                _console.report({'INFO'}, b_child.name)
            elif not b_child.name in arr_ignore:
                _console.report({'INFO'}, "Moving bone "+b_child.name)
                b=arm.edit_bones[b_child.name]
                changes=mathutils.Vector((b.head[0]-b_child.head[0],
                    b.head[1]-b_child.head[1],
                    b.head[2]-b_child.head[2]))
                b.tail = [b.tail[0]-b.head[0]+b_child.head[0],
                    b.tail[1]-b.head[1]+b_child.head[1],
                    b.tail[2]-b.head[2]+b_child.head[2]]
                b.head = b_child.head
                #b.matrix = b_child.matrix
                #b.parent = b_child.parent
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
            if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
                if not context.scene.fdk_source_armature and bpy.context.selected_objects:
                    for (idx, obj) in enumerate(bpy.context.selected_objects):
                        if not obj.name == bpy.context.active_object.name and obj.type == "ARMATURE":
                            context.scene.fdk_source_armature=bpy.context.selected_objects[idx]
            arm0 = bpy.data.objects.get(context.scene.fdk_source_armature.name).data
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.get(context.scene.fdk_source_armature.name).select_set(True)
        bpy.data.objects.get(context.scene.fdk_target_armature.name).select_set(True)
        bpy.context.view_layer.objects.active=bpy.data.objects.get(context.scene.fdk_target_armature.name)
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
    bl_label = "根据JSON重命名骨骼"
    bl_description = "根据JSON重命名骨骼"
    
    def execute(self, context):
        if not "fdk_rename_pair_json_data" in context.scene or context.scene["fdk_rename_pair_json_data"] == "":
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        rename_pair=json.loads(context.scene["fdk_rename_pair_json_data"])
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object and bpy.context.active_object.type == "ARMATURE":
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
        
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
class O_hideEmpty(bpy.types.Operator):
    bl_idname = "fdktools.hide_empty_object"
    bl_label = "隐藏空物体"
    bl_description = "隐藏空物体"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
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
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.type == "EMPTY":
                obj.hide_set(False)
                
        self.report({'INFO'},f"O_showEmpty finished")
        return {'FINISHED'}
        
class O_delEmpty(bpy.types.Operator):
    bl_idname = "fdktools.remove_empty_object"
    bl_label = "移除空物体（慎用！）"
    bl_description = "移除空物体（慎用！）"
    
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
        
class O_resetEmptyRot(bpy.types.Operator):
    bl_idname = "fdktools.reset_empty_object"
    bl_label = "重设空物体旋转"
    bl_description = "重设空物体旋转"
    
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
        
class O_del_glTF_not(bpy.types.Operator):
    bl_idname = "fdktools.remove_gltf_collection"
    bl_label = "清理glTF_not_exported"
    bl_description = "清理glTF_not_exported"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        collection = bpy.data.collections.get('glTF_not_exported')
        bpy.data.collections.remove(collection)
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                for bone in obj.pose.bones:
                    bone.custom_shape = None
        self.report({'INFO'},f"O_del_glTF_not finished")
        return {'FINISHED'}
########################## Divider ##########################
class O_join_Meshes(bpy.types.Operator):
    #TODO: 支持忽略顶点组
    bl_idname = "fdktools.join_selected_meshes"
    bl_label = "JOIN & DELETE"
    bl_description = "先选新的，再选旧的，然后JOIN"
    
    def execute(self, context):
        try:
            if not context.scene.fdk_target_mesh and bpy.context.active_object and bpy.context.active_object.type=="MESH":
                context.scene.fdk_target_mesh = bpy.context.active_object
            if not context.scene.fdk_source_mesh:
                for (idx, obj) in enumerate(bpy.context.selected_objects):
                    if not obj.name == bpy.context.active_object.name and obj.type == "MESH":
                        context.scene.fdk_source_mesh = bpy.context.selected_objects[idx]
            mesh0 = bpy.data.objects.get(context.scene.fdk_source_mesh.name)
            mesh = bpy.data.objects.get(context.scene.fdk_target_mesh.name)
        except:
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
        context.scene.fdk_source_mesh=None
        context.scene.fdk_target_mesh=None
        self.report({'INFO'},f"O_join_Meshes finished")
        return {'FINISHED'}
########################## Divider ##########################
#TODO: 导出材质和贴图名
########################## Divider ##########################
class P_FDK_Snippets(bpy.types.Panel):
    bl_idname = "FDK_Snippets"
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
        col.operator(O_AssignArmature.bl_idname, text=O_AssignArmature.bl_label, icon="ARMATURE_DATA")
        col.prop(context.scene, "fdk_target_armature", text="目标骨架", icon="ARMATURE_DATA")
        if context.scene.fdk_config_json_data:
            box = layout.box()
            col = box.column()
            col.prop(context.scene, "fdk_source_armature", text="源骨架", icon="ARMATURE_DATA")
            if context.scene.fdk_source_armature:
                col.operator(O_CopyBone.bl_idname, text=O_CopyBone.bl_label, icon="BONE_DATA")#复制位置
            else:
                col.label(text="先选择目标骨架才能复制位置")

class P_FDK_Snippets_Target(bpy.types.Panel):
    bl_idname = "FDK_Snippets_Target"
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
        if context.scene.fdk_target_armature:
            col = box.column(align=True)
            col.label(text="指定父级骨骼")
            col.prop(context.scene, 'fdk_modify_headname')
            row = col.row(align=True)
            row.operator(O_DelBone.bl_idname, text=O_DelBone.bl_label, icon="BONE_DATA")#删除子级
            row.operator(O_DelOtherBone.bl_idname, text=O_DelOtherBone.bl_label, icon="BONE_DATA")#删除其他
            
            box = layout.box()
            col = box.column(align=True)
            if context.scene.fdk_config_json_data:
                col.operator(O_RenameBone.bl_idname, text=O_RenameBone.bl_label, icon="BONE_DATA")#重命名子级
                col.operator(O_AddEmpty.bl_idname, text=O_AddEmpty.bl_label, icon="EMPTY_DATA")#添加空物体
            else:
                col.operator(O_ImportJSON.bl_idname, icon="IMPORT", text="脸部改名/添加空物体需先选择配置JSON")
                
            box = layout.box()
            col = box.column(align=True)
            col.label(text="依replace_dict.json重命名目标骨架")
            col.operator(O_ImportRenameJSON.bl_idname, icon="IMPORT")#重命名配对JSON
            if context.scene.fdk_rename_pair_json_data:
                col.operator(O_RenameByJSON.bl_idname, text=O_RenameByJSON.bl_label, icon="BONE_DATA")
        else:
            col = box.column(align=True)
            col.label(text="先选择目标骨架才能操作")


class P_FDK_Snippets_Others(bpy.types.Panel):
    bl_idname = "FDK_Snippets_Others"
    bl_label = "其他快捷"
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
        row = col.row(align=True)
        row.operator(O_delEmpty.bl_idname, text=O_delEmpty.bl_label, icon="EMPTY_DATA")
        row.operator(O_resetEmptyRot.bl_idname, text=O_resetEmptyRot.bl_label, icon="EMPTY_DATA")
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, "fdk_source_mesh", text="源网格", icon="MESH_DATA")
        col.prop(context.scene, "fdk_target_mesh", text="目标网格", icon="MESH_DATA")
        col.operator(O_join_Meshes.bl_idname, text=O_join_Meshes.bl_label, icon="MESH_DATA")
########################## Divider ##########################
def register():
    bpy.utils.register_class(O_AssignArmature)
    bpy.utils.register_class(O_ImportJSON)
    bpy.utils.register_class(O_ImportRenameJSON)
    bpy.utils.register_class(O_DelBone)
    bpy.utils.register_class(O_DelOtherBone)
    bpy.utils.register_class(O_RenameBone)
    bpy.utils.register_class(O_CopyBone)
    bpy.utils.register_class(O_AddEmpty)
    bpy.utils.register_class(O_RenameByJSON)
    
    bpy.utils.register_class(O_hideEmpty)
    bpy.utils.register_class(O_showEmpty)
    bpy.utils.register_class(O_delEmpty)
    bpy.utils.register_class(O_resetEmptyRot)
    bpy.utils.register_class(O_del_glTF_not)
    bpy.utils.register_class(O_join_Meshes)
    
    bpy.utils.register_class(P_FDK_Snippets)
    bpy.utils.register_class(P_FDK_Snippets_Target)
    bpy.utils.register_class(P_FDK_Snippets_Others)
    
    bpy.types.Scene.fdk_config_json_data = bpy.props.StringProperty(
        name="Config JSON Data",description="配置数据",default=""
    )
    bpy.types.Scene.fdk_rename_pair_json_data = bpy.props.StringProperty(
        name="Rename JSON Data",description="重命名配对数据",default=""
    )
    bpy.types.Scene.fdk_source_armature = bpy.props.PointerProperty(
        description="选择一个骨架作为数据源",type=bpy.types.Object,poll=ObjType.is_armature
    )
    bpy.types.Scene.fdk_target_armature = bpy.props.PointerProperty(
        description="选择将被作用的骨架",type=bpy.types.Object,poll=ObjType.is_armature
    )
    bpy.types.Scene.fdk_modify_headname = bpy.props.StringProperty(
        name="名字",description="设置父级名字",default= "Head"
    )
    bpy.types.Scene.fdk_source_mesh = bpy.props.PointerProperty(
        description="选择一个网格作为数据源",type=bpy.types.Object,poll=ObjType.is_mesh
    )
    bpy.types.Scene.fdk_target_mesh = bpy.props.PointerProperty(
        description="选择将被作用的网格",type=bpy.types.Object,poll=ObjType.is_mesh
    )

def unregister():
    bpy.utils.unregister_class(O_AssignArmature)
    bpy.utils.unregister_class(O_ImportJSON)
    bpy.utils.unregister_class(O_ImportRenameJSON)
    bpy.utils.unregister_class(O_DelBone)
    bpy.utils.unregister_class(O_DelOtherBone)
    bpy.utils.unregister_class(O_RenameBone)
    bpy.utils.unregister_class(O_CopyBone)
    bpy.utils.unregister_class(O_AddEmpty)
    bpy.utils.unregister_class(O_RenameByJSON)
    
    bpy.utils.unregister_class(O_hideEmpty)
    bpy.utils.unregister_class(O_showEmpty)
    bpy.utils.unregister_class(O_delEmpty)
    bpy.utils.unregister_class(O_resetEmptyRot)
    bpy.utils.unregister_class(O_del_glTF_not)
    bpy.utils.unregister_class(O_join_Meshes)
    
    bpy.utils.unregister_class(P_FDK_Snippets)
    bpy.utils.unregister_class(P_FDK_Snippets_Target)
    bpy.utils.unregister_class(P_FDK_Snippets_Others)

    del bpy.types.Scene.fdk_config_json_data
    del bpy.types.Scene.fdk_rename_pair_json_data
    del bpy.types.Scene.fdk_source_armature
    del bpy.types.Scene.fdk_target_armature
    del bpy.types.Scene.fdk_source_mesh
    del bpy.types.Scene.fdk_target_mesh
    del bpy.types.Scene.fdk_modify_headname
    