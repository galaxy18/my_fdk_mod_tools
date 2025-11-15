bl_info = {
    "name": "FDK Snippets",
    "author": "",
    "version": (1, 0, 3),
    "blender": (4, 2, 3),
    "location": "View3D > Tool Shelf >FDK_Snippets Panel",
    "description": "FDK MOD制作 快捷代码",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}
#1.01:取消拾取框改为固定使用活动物体，新增复制贴图功能
#1.02:取消隐藏按钮，改为变灰，改善视觉感受
#1.03:添加清理无顶点组骨骼（未测试是否会造成问题）
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

