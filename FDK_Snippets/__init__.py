bl_info = {
    "name": "FDK Snippets",
    "author": "",
    "version": (1, 0, 6),
    "blender": (4, 2, 3),
    "location": "View3D > Tool Shelf >FDK_Snippets Panel",
    "description": "FDK MOD制作 快捷代码",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}
#1.01:取消拾取框改为固定使用活动物体，新增复制贴图信息
#1.02:无效的按钮从隐藏改为变灰，改善视觉感受
#1.03:添加清理无顶点组骨骼（未测试是否会造成问题）
#1.04:增加了清理无顶点组骨骼时，要忽略的顶点组的配置项。增加了一种重置空物体旋转选项。
#1.05:增加了复制一个空物体旋转和缩放值到另一个空物体。
#1.06:为修复动画重定向中的问题，增加了不用读取配置json，直接对比两个骨架复制缺少的骨节。
########################## Divider ##########################
from . import panel

# 注册插件
def register():
    panel.register()

# 注销插件
def unregister():
    panel.unregister()

if __name__ == "__main__":
    register()

