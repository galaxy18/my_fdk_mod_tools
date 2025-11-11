bl_info = {
    "name": "FDK Snippets",
    "author": "",
    "version": (1, 0),
    "blender": (4, 2, 3),
    "location": "View3D > Tool Shelf >FDK_Snippets Panel",
    "description": "FDK Snippets",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}
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

