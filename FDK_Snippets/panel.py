# type: ignore
import bpy,re,os
import csv, json
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
class O_ImportJSON(bpy.types.Operator, ImportHelper):
    bl_idname = "fdktools.json_import"
    bl_label = "导入配置JSON"
    bl_description = "导入时右上角选择编码格式"
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
                    config=json.load(file)
                    context.scene["copy_bone_config"]=config
                
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
class O_DelBone(bpy.types.Operator):
    bl_idname = "fdktools.remove_head_bones"
    bl_label = "删除头部骨骼"
    bl_description = "删除头部骨骼"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object:
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if arm.edit_bones.get(headkey) is not None:
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            bpy.ops.armature.delete()
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            self.report({'ERROR'}, "所选骨架中不存在"+headkey)
            return {'FINISHED'}
        return {'FINISHED'}
        
class O_RenameBone(bpy.types.Operator):
    bl_idname = "fdktools.rename_head_bones"
    bl_label = "重命名脸部顶点组"
    bl_description = "重命名脸部顶点组，复制一份原名骨骼以应对定位"

    def execute(self, context):
        headkey=context.scene.fdk_modify_headname
        if not "copy_bone_config" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            arr_copy=context.scene["copy_bone_config"]["RenameBone_arr_copy"]["data"]
            arr_copy_ignore=context.scene["copy_bone_config"]["RenameBone_arr_copy_ignore"]["data"]
            
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object:
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择对象骨架") 
            return {'FINISHED'}
            
        bpy.ops.object.mode_set(mode='EDIT')
        newbones=[]
        for bonename in arr_copy:
            bpy.ops.armature.select_all(action='DESELECT')
            try:
                arm.edit_bones.active = arm.edit_bones[bonename]
                #print(bpy.context.selected_editable_bones[0].name)
                b = bpy.context.selected_editable_bones[0]
                cb = arm.edit_bones.new(bonename+"_Copy")
                cb.head = b.head
                cb.tail = b.tail
                cb.matrix = b.matrix
                cb.parent = b.parent
                newbones.append(cb)
                if headkey=="":
                    arm.edit_bones[bonename].name=bonename+"_Orig"
            except:
                print('')

        if not headkey=="":
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            arm.edit_bones.active = arm.edit_bones[headkey]
            bpy.ops.armature.select_similar(type='CHILDREN')
            for obj in bpy.context.selected_editable_bones:
                if not (obj.name in arr_copy_ignore or obj.name.endswith("_Copy") or obj.name.endswith("_New") or obj.name.endswith("_Orig")):
                    oldname = obj.name
                    obj.name = oldname+"_New"

        for obj in newbones:
            obj.name = obj.name.replace("_Copy", "")

        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}
        
class O_AddEmpty(bpy.types.Operator):
    bl_idname = "fdktools.add_empty_objects"
    bl_label = "向目标骨架添加空物体"
    bl_description = "向目标骨架添加空物体"
    
    def execute(self, context):
        if not "copy_bone_config" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            arr_addPoint=context.scene["copy_bone_config"]["AddEmpty_arr_addPoint"]["data"]
        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object:
                context.scene.fdk_target_armature = bpy.context.active_object
            arm = bpy.data.objects.get(context.scene.fdk_target_armature.name).data
        except:
            self.report({'ERROR'}, "没有选择目标骨架") 
            return {'FINISHED'}
        
        for obj in arr_addPoint:
            if not obj[0] in bpy.data.objects:
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")
                bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD", location=(0, 0, 0), scale=(1, 1, 1))
                #ae = bpy.context.active_object
                bpy.context.active_object.name = obj[0]
                if obj[1] in bpy.data.objects:
                    if obj[2] == "BONE":
                        bpy.context.active_object.parent = arm.name
                        bpy.context.active_object.parent_type = "BONE"
                        if obj[3] in arm.bones :
                            bpy.context.active_object.parent_bone = obj[3]
                            bpy.context.active_object.location = arm.bones[obj[3]].tail
                        else:
                            print ("Error:"+obj[0]+": parent bone "+obj[3]+" not exist")
                    else:
                        bpy.context.active_object.parent = bpy.data.objects[obj[1]]
                        bpy.context.active_object.parent_type = obj[2]
                else:
                    print("Error:"+obj[0]+": parent node "+obj[1]+" not exist")
                #math.sin(math.pi/4)
                bpy.context.active_object.rotation_mode = "QUATERNION"
                #bpy.context.active_object.rotation_quaternion = Quaternion([math.sin(math.pi/4),-math.sin(math.pi/4),0,0])
                bpy.context.active_object.rotation_quaternion = Quaternion([1,0,0,0])
                bpy.context.active_object.scale = [1.0,1.0,1.0]
                bpy.context.object.lock_scale = [True,True,True]
            else:
                print("Info:"+obj[0]+": "+obj[0]+" already exists")
        return {'FINISHED'}
    
class O_CopyBone(bpy.types.Operator):
    bl_idname = "fdktools.copy_bone_nodes"
    bl_label = "复制位置"
    bl_description = "复制位置"

    def create_Bone(_console, _context, arm0, arm, b_orig):
        arr_add_ignore = _context.scene["copy_bone_config"]["CopyBone_arr_add_ignore"]["data"]
        if (arm.edit_bones.get(b_orig.name) is None) and (not b_orig.name in arr_add_ignore):
            # _console.report({'INFO'}, '    creating '+b_orig.name)
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if arm.edit_bones.get(b_orig.parent.name) is None:
                O_CopyBone.create_Parent(arm0, arm, b_orig.parent)
            b.parent = arm.edit_bones[b_orig.parent.name]
        for child in b_orig.children:
            O_CopyBone.create_Bone(_console, _context, arm0, arm, child)

    def create_Parent(arm0, arm, b_orig):
        # _console.report({'INFO'}, '        Info: creating parent bone '+b_orig.name+' can not be skipped')
        if arm.edit_bones.get(b_orig.name) is None:
            b = arm.edit_bones.new(b_orig.name)
            b.head = b_orig.head
            b.tail = b_orig.tail
            b.matrix = b_orig.matrix
            if arm.edit_bones.get(b_orig.parent.name) is None:
                O_CopyBone.create_Parent(arm0, arm, b_orig.parent)
            b.parent = arm.edit_bones[b_orig.parent.name]

    def processname(_console, _context, arm0, arm, b_child, processchild=True):
        arr_ignore = _context.scene["copy_bone_config"]["CopyBone_arr_ignore"]["data"]
        changes=mathutils.Vector((0,0,0))
        try:
            if arm.edit_bones.get(b_child.name) is None:
                O_CopyBone.create_Bone(_console, _context, arm0, arm, b_child)
                #console.report({'INFO'}, b_child.name)
            elif not b_child.name in arr_ignore:
                # _console.report({'INFO'}, "Moving bone "+b_child.name)
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
                    # _console.report({'INFO'}, "    Moving EMPTY obj: " + obj.name+" "+changes)
                    obj.rotation_quaternion = Quaternion([1,0,0,0])
                    obj.scale = [1.0,1.0,1.0]
                    obj.location += changes
        except Exception as e: _console.report({'INFO'}, e)
        if processchild:
            for child in b_child.children:
                O_CopyBone.processname(_console, _context, arm0, arm, child)

    def execute(self, context):
        if not "copy_bone_config" in context.scene:
            self.report({'ERROR'}, "没有选择配置文件") 
            return {'FINISHED'}
        else:
            arr_base=context.scene["copy_bone_config"]["CopyBone_arr_base"]["data"]
            arr_names=context.scene["copy_bone_config"]["CopyBone_arr_names"]["data"]
            arr_add=context.scene["copy_bone_config"]["CopyBone_arr_add"]["data"]

        try:
            if not context.scene.fdk_target_armature and bpy.context.active_object:
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

        # for (idx, obj) in enumerate(bpy.context.selected_objects):
            # if obj.name == bpy.context.active_object.name:
                # arm=bpy.context.selected_objects[idx].data
            # elif obj.type == "ARMATURE":
                # arm0=bpy.context.selected_objects[idx].data
                
        bpy.ops.object.mode_set(mode='EDIT')
        for basename in arr_base:
            O_CopyBone.processname(self, context, arm0, arm, arm0.edit_bones[basename])
            
        for basename in arr_names:
            O_CopyBone.processname(self, context, arm0, arm, arm0.edit_bones[basename],False)
            
        for basename in arr_add:
            b0 = arm0.edit_bones.get(basename)
            if b0 is not None:
                O_CopyBone.create_Bone(self, context, arm0, arm, b0)
                
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}
########################## Divider ##########################
class O_AssignArmature(bpy.types.Operator):
    bl_idname = "fdktools.assign_armature"
    bl_label = "根据选择设置物体"
    bl_description = "根据选择设置物体"
    def execute(self, context):
        try:
            context.scene.fdk_target_armature = bpy.context.active_object
            for (idx, obj) in enumerate(bpy.context.selected_objects):
                if not obj.name == bpy.context.active_object.name and obj.type == "ARMATURE":
                    context.scene.fdk_source_armature=bpy.context.selected_objects[idx]
        except:
            return {'FINISHED'}
        return {'FINISHED'}
########################## Divider ##########################
class P_FDK_Snippets(bpy.types.Panel):
    bl_idname = "FDK_Snippets"
    bl_label = "FDK编辑工具"
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
        col.prop(context.scene, "fdk_source_armature", text="源骨架", icon="ARMATURE_DATA")
        col.prop(context.scene, "fdk_target_armature", text="目标骨架", icon="ARMATURE_DATA")
        col.operator(O_AssignArmature.bl_idname, text=O_AssignArmature.bl_label, icon="ARMATURE_DATA")
        
        box = layout.box()
        col = box.column(align=True)
        col.operator(O_ImportJSON.bl_idname, icon="IMPORT")
        
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, 'fdk_modify_headname')
        row = col.row(align=True)
        row.operator(O_DelBone.bl_idname, text=O_DelBone.bl_label, icon="BONE_DATA")
        row.operator(O_RenameBone.bl_idname, text=O_RenameBone.bl_label, icon="BONE_DATA")
        
        box = layout.box()
        col = box.column(align=True)
        col.operator(O_CopyBone.bl_idname, text=O_CopyBone.bl_label, icon="BONE_DATA")
        col.operator(O_AddEmpty.bl_idname, text=O_AddEmpty.bl_label, icon="EMPTY_DATA")
########################## Divider ##########################
def register():
    bpy.utils.register_class(O_AssignArmature)
    bpy.utils.register_class(O_ImportJSON)
    bpy.utils.register_class(O_DelBone)
    bpy.utils.register_class(O_RenameBone)
    bpy.utils.register_class(O_CopyBone)
    bpy.utils.register_class(O_AddEmpty)
    bpy.utils.register_class(P_FDK_Snippets)
    
    bpy.types.Scene.fdk_config_json_data = bpy.props.StringProperty(
        name="Config JSON Data",
        description="Stores imported JSON data",
        default=""
    )
    bpy.types.Scene.fdk_source_armature = bpy.props.PointerProperty(
        description="选择一个骨架作为数据目标",
        type=bpy.types.Object, 
        poll=ObjType.is_armature
    )
    bpy.types.Scene.fdk_target_armature = bpy.props.PointerProperty(
        description="选择将被作用的骨架",
        type=bpy.types.Object, 
        poll=ObjType.is_armature
    )
    bpy.types.Scene.fdk_modify_headname = bpy.props.StringProperty(name="父级骨骼:", default= "Head")

def unregister():
    bpy.utils.unregister_class(O_AssignArmature)
    bpy.utils.unregister_class(O_ImportJSON)
    bpy.utils.unregister_class(O_DelBone)
    bpy.utils.unregister_class(O_RenameBone)
    bpy.utils.unregister_class(O_CopyBone)
    bpy.utils.unregister_class(O_AddEmpty)
    bpy.utils.unregister_class(P_FDK_Snippets)

    del bpy.types.Scene.fdk_config_json_data
    del bpy.types.Scene.fdk_source_armature
    del bpy.types.Scene.fdk_target_armature
    del bpy.types.Scene.fdk_modify_headname