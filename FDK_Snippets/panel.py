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
                    if "Headkey" in fdk_config_json_data and (not fdk_config_json_data["Headkey"]==""):
                        context.scene.fdk_modify_headname=fdk_config_json_data["Headkey"]
                    if "RenameBone_prefix" in fdk_config_json_data and (not fdk_config_json_data["RenameBone_prefix"]==""):
                        context.scene.fdk_rename_prefix=fdk_config_json_data["RenameBone_prefix"]
                    # if "RenameBone_copy_prefix" in fdk_config_json_data:
                        # context.scene.fdk_rename_copy_prefix=fdk_config_json_data["RenameBone_copy_prefix"]
                    if "RenameBone_orig_prefix" in fdk_config_json_data and (not fdk_config_json_data["RenameBone_orig_prefix"]==""):
                        context.scene.fdk_rename_orig_prefix=fdk_config_json_data["RenameBone_orig_prefix"]
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
        resetempty=_context.scene["resetempty"]
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
                if changetail == True:
                    b.tail = [b.tail[0]-b.head[0]+b_child.head[0],
                        b.tail[1]-b.head[1]+b_child.head[1],
                        b.tail[2]-b.head[2]+b_child.head[2]]
                else:
                    b.tail = b_child.tail
                b.head = b_child.head
                if changematrix==True:
                    b.matrix = b_child.matrix
                #b.parent = b_child.parent
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
            changematrix=context.scene["reset_empty"]
        except:
            context.scene["reset_empty"]=True
        try:
            changematrix=context.scene["change_tail"]
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
        target = bpy.context.active_object
        # source.hide_set(False)
        # target.hide_set(False)
        for obj in bpy.context.selected_objects:
            if obj.name != target.name:
                source = obj
        target.rotation_quaternion = source.rotation_quaternion
        target.scale = source.scale
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
    bl_description = "（实验功能）删除无顶点组的骨骼"
    
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
        self.report({'INFO'},f"O_remove_Empty_Bone collecting...")
        for bone in arm.edit_bones:
            if bone.name in bones:
                if bone.name in arr_shouldkeep:
                    self.report({'INFO'},f"{bone.name} keeped")
                else:
                    bone.select = True
                    bone.select_head = True
                    bone.select_tail = True
                    self.report({'INFO'},f"{bone.name} removed")
        bpy.ops.armature.delete()
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'},f"O_remove_Empty_Bone finished")
        return {'FINISHED'}
    
########################## Divider ##########################
class O_compare_Armatures(bpy.types.Operator):
    bl_idname = "fdktools.compare_arms"
    bl_label = "提取骨骼名称差异"
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
        O_CopyBonecol.operator(O_compare_Armatures.bl_idname, text=O_compare_Armatures.bl_label, icon="COPYDOWN")#对比骨架
        
        O_CopyBonecol.operator(O_CopyBone.bl_idname, text=O_CopyBone.bl_label, icon="ARMATURE_DATA")#复制位置
        
        # row = O_CopyBonecol.row(align=True)
        # row.prop(context.scene, "change_matrix", text="copy_matrix")
        # row.prop(context.scene, "change_tail", text="copy_tail")
        # row.prop(context.scene, "reset_empty", text="reset_empty")
                
        if (not (bpy.context.active_object and bpy.context.active_object.type=="ARMATURE")) or (sel_obj is None):
            O_CopyBonecol.enabled=False
            col.label(text="先选择骨架才能操作")
        elif not context.scene.fdk_config_json_data:
            O_CopyBonecol.enabled=False
            col.label(text="先导入JSON才能操作")
                        
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

class P_FDK_Snippets_Others(bpy.types.Panel):
    bl_idname = "FDK_Snippets_Others"
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
        
        # col.prop(context.scene, "fdk_source_mesh", text="源网格", icon="MESH_DATA")
        # col.prop(context.scene, "fdk_target_mesh", text="目标网格", icon="MESH_DATA")
        # col.operator(O_join_Meshes.bl_idname, text=O_join_Meshes.bl_label, icon="MESH_DATA")
########################## Divider ##########################
def register():
    # bpy.utils.register_class(O_AssignArmature)
    bpy.utils.register_class(O_ImportJSON)
    bpy.utils.register_class(O_ImportRenameJSON)
    bpy.utils.register_class(O_DelBone)
    bpy.utils.register_class(O_DelOtherBone)
    bpy.utils.register_class(O_select_Meshes_By_Armature)
    bpy.utils.register_class(O_unselect_Meshes_By_Armature)
    bpy.utils.register_class(O_RenameBone)
    bpy.utils.register_class(O_CopyBone)
    bpy.utils.register_class(O_compare_Armatures)
    bpy.utils.register_class(O_AddEmpty)
    bpy.utils.register_class(O_RenameByJSON)
    
    bpy.utils.register_class(O_hideEmpty)
    bpy.utils.register_class(O_showEmpty)
    bpy.utils.register_class(O_delEmpty)
    bpy.utils.register_class(O_resetEmptyRot1)
    bpy.utils.register_class(O_resetEmptyRot2)
    bpy.utils.register_class(O_copyEmptyRot)
    bpy.utils.register_class(O_del_glTF_not)
    bpy.utils.register_class(O_join_Meshes)
    bpy.utils.register_class(O_get_MaterialName)
    bpy.utils.register_class(O_get_Names_By_Armature)
    bpy.utils.register_class(O_remove_Empty_Bone)
    
    bpy.utils.register_class(P_FDK_Snippets)
    bpy.utils.register_class(P_FDK_Snippets_Target)
    bpy.utils.register_class(P_FDK_Snippets_Others)
    
    bpy.types.Scene.fdk_config_json_data = bpy.props.StringProperty(
        name="Config JSON Data",description="配置数据",default=""
    )
    bpy.types.Scene.fdk_rename_pair_json_data = bpy.props.StringProperty(
        name="Rename JSON Data",description="重命名配对数据",default=""
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

def unregister():
    # bpy.utils.unregister_class(O_AssignArmature)
    bpy.utils.unregister_class(O_ImportJSON)
    bpy.utils.unregister_class(O_ImportRenameJSON)
    bpy.utils.unregister_class(O_DelBone)
    bpy.utils.unregister_class(O_DelOtherBone)
    bpy.utils.unregister_class(O_select_Meshes_By_Armature)
    bpy.utils.unregister_class(O_unselect_Meshes_By_Armature)
    bpy.utils.unregister_class(O_RenameBone)
    bpy.utils.unregister_class(O_CopyBone)
    bpy.utils.unregister_class(O_compare_Armatures)
    bpy.utils.unregister_class(O_AddEmpty)
    bpy.utils.unregister_class(O_RenameByJSON)
    
    bpy.utils.unregister_class(O_hideEmpty)
    bpy.utils.unregister_class(O_showEmpty)
    bpy.utils.unregister_class(O_delEmpty)
    bpy.utils.unregister_class(O_resetEmptyRot1)
    bpy.utils.unregister_class(O_resetEmptyRot2)
    bpy.utils.unregister_class(O_copyEmptyRot)
    bpy.utils.unregister_class(O_del_glTF_not)
    bpy.utils.unregister_class(O_join_Meshes)
    bpy.utils.unregister_class(O_get_MaterialName)
    bpy.utils.unregister_class(O_get_Names_By_Armature)
    bpy.utils.unregister_class(O_remove_Empty_Bone)
    
    bpy.utils.unregister_class(P_FDK_Snippets)
    bpy.utils.unregister_class(P_FDK_Snippets_Target)
    bpy.utils.unregister_class(P_FDK_Snippets_Others)

    del bpy.types.Scene.fdk_config_json_data
    del bpy.types.Scene.fdk_rename_pair_json_data
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