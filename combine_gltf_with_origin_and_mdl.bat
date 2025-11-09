rmdir /S /Q %1

IF EXIST %1.glb (
  py kuro_gltf_to_meshes.py %1.glb
) ELSE (
  py kuro_gltf_to_meshes.py %1.gltf
)

cd %2
del /Q *.fmt
del /Q *.vb
del /Q *.ib
del /Q *.vgmap

cd ..

xcopy /s /Y %1 %2

move /Y "%USERPROFILE%\Downloads\material_info.json" %2
py kuro_mdl_import_meshes.py %2.mdl

copy %2.mdl "D:\SteamLibrary\steamapps\common\Sora No Kiseki the 1st\asset\common\model"

IF NOT 'pause' == '%3' goto end

pause

:end