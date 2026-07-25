bl_info = {
    "name": "FDK Snippets",
    "author": "",
    "version": (1, 0, 10),
    "blender": (4, 2, 3),
    "location": "View3D > Tool Shelf >FDK_Snippets Panel",
    "description": "FDK MOD制作 快捷代码",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}
#1.0.1:取消拾取框改为固定使用活动物体，新增复制贴图信息
#1.0.2:无效的按钮从隐藏改为变灰，改善视觉感受
#1.0.3:添加清理无顶点组骨骼（未测试是否会造成问题）
#1.0.4:增加了清理无顶点组骨骼时，要忽略的顶点组的配置项。增加了一种重置空物体旋转选项。
#1.0.5:增加了复制一个空物体旋转和缩放值到另一个空物体。
#1.0.6:为修复动画重定向中的问题，增加了不用读取配置json，直接对比两个骨架复制缺少的骨节。
#1.0.7:增加将选取的骨架复制为活动骨架的选中骨节的子级和将贴图后缀名改成png/dds;bug fix
#1.0.8:增加选取两段骨节复制位置
#1.0.9:将FGOA相关命令移到单独的分页；增加根据json修改骨架父子层级
#1.1.0:将转换mdl系列命令整合为按钮，调用kuro_mdl_tool v1.6.5
#1.1.1:增加将mdl转换为gltf格式之后直接导入的测试功能，调用io_scene_gltf2 v5.2.11
#1.1.2:增加贴图不改为png和不对原mdl进行备份的选项
#1.1.3:直接调用移除glTF_not_exported
#1.1.4:增加直接输出为vb+ib文件夹；提取json调整为只输出2个不会被覆盖的json；增加提取metadata
#1.1.5:将输出为vb+ib文件夹的设置从自定义文件名改为选择输出文件夹；增加简易对比材质json
#1.1.6:增加导入json数据。由于展示数据会使选项面板显得太长，将面板划分为三个。
#1.1.7:增加导入新json前保存当前配置。增加删除配置按钮。
#1.1.8:尝试不依靠输出文件更新mdl
#1.1.9:支持选取.mdl.bak文件；修复了作者忘了给变量改个独特点的名字的问题
#1.1.10:kuro_mdl_tools更新到v166 支持京轨的mdl v5
########################## Divider ##########################
from . import panel, sub_kuro_mdl_tools, sub_others

# 注册插件
def register():
    panel.register()
    sub_kuro_mdl_tools.register()
    sub_others.register()

# 注销插件
def unregister():
    panel.unregister()
    sub_kuro_mdl_tools.unregister()
    sub_others.unregister()

if __name__ == "__main__":
    register()

