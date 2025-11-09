chcp 65001
@echo off

IF '%1' EQU '' GOTO printhelp

set gamebase=D:\data\
set keepfiles=N
set toV1=N
for /F "tokens=1,2,3" %%i in (config.ini) do call :processconf %%i %%j %%k
IF "%2" EQU "inject" set toV1=Y
IF "%3" EQU "keepfiles" set keepfiles=Y

::set gamebase
::set gamemdlfolder
::set gameimgfolder
::set extract_prefix
IF %1 EQU ed92cle GOTO inited92cle
IF %1 EQU ed93cle GOTO inited93cle

IF %1 EQU ys10cle GOTO initys10cle
IF %1 EQU ys10pcle GOTO initys10pcle
IF %1 EQU ys10nisa GOTO initys10nisa

IF %1 EQU sora1cle GOTO initsora1cle
GOTO printhelp

:endofsetting
@echo on
set base=%~dp0
set /P charaid=File ID:

IF EXIST %charaid% rmdir /s /q %charaid%
IF EXIST %gamemdlfolder%\%charaid%.mdl" (
  copy %gamemdlfolder%\%charaid%.mdl"
  set extract_folder=%extract_prefix%_%charaid%
  copy %gamemdlfolder%_info\%charaid%.mi"
) ELSE (
echo %gamemdlfolder%\%charaid%.mdl" not exists
GOTO end
)
:convert
python runtime/cle_decrypt_decompress.py "%base%\%charaid%.mdl"
python runtime/kuro_mdl_to_basic_gltf.py "%base%\%charaid%.mdl"
python runtime/kuro_mdl_export_meshes.py "%base%\%charaid%.mdl"
python runtime/kuro_decode_bin_json.py "%base%\%charaid%.mi"
IF %toV1% EQU Y (
  python runtime/kuro_mdl_import_meshes.py -f 1 "%base%\%charaid%.mdl"
  cd ./runtime
  ED9MDLTool.exe "%base%\%charaid%.mdl"
  IF NOT EXIST %charaid%.fbx (
    @echo can not convert %charaid%.fbx
  )
  IF EXIST %charaid%.fbx (
    move %charaid%.fbx "%base%"
  )
  cd ../
)

set imgbase=%charaid%_img
IF EXIST %imgbase% rmdir /s /q %imgbase%
mkdir %imgbase%

for /F "tokens=1,2,3" %%i in (%charaid%\image_list.json) do call :process %%i %%j %%k 
GOTO keepfiles

:process
set VAR1=%1
if %VAR1%==[ GOTO next
if %VAR1%==] GOTO next
IF NOT EXIST %gameimgfolder%\%VAR1:~1,-1%" (
  @echo %gameimgfolder%\%VAR1:~1,-1%" not exist
)
copy %gameimgfolder%\%VAR1:~1,-1%" %imgbase%
:next
GOTO :EOF

:processconf
if %1 EQU gamebase set gamebase=%2
IF %1 EQU keepfiles if %2 EQU Y set keepfiles=Y
IF %1 EQU toV1 if %2 EQU Y set toV1=Y
:next
GOTO :EOF

:keepfiles
:processDDS
set pngbase=textures
IF EXIST %pngbase% rmdir /s /q %pngbase%
mkdir %pngbase%
cd "compressonatorcli-4.5.52-win64"
for /r %base%%imgbase% %%i in (*.dds) do (
  copy /Y %%i .
  compressonatorcli.exe %%~nxi %%~ni.png
  move /Y %%~ni.png %base%%pngbase%
  del /Q %%~nxi
)
cd ../

IF %keepfiles% EQU Y (
  IF EXIST %extract_folder% rmdir /s /q %extract_folder%
  mkdir %extract_folder%
  move %charaid% %extract_folder%
  move %charaid%_img %extract_folder%
  move %pngbase% %extract_folder%
  move %charaid%.mdl %extract_folder%
  move %charaid%.glb %extract_folder%
  move %charaid%.gltf %extract_folder%
  move %charaid%.bin %extract_folder%
  move %charaid%.metadata %extract_folder%
  move %charaid%.mi %extract_folder%
  move %charaid%.json %extract_folder%
  IF EXIST %charaid%.mdl.original_encrypted move %charaid%.mdl.original_encrypted %extract_folder%
  IF EXIST %charaid%.fbx move %charaid%.fbx %extract_folder%
  IF EXIST %charaid%.mdl.bak move %charaid%.mdl.bak %extract_folder%
  echo Process finished
  GOTO end
)
::else
set /P REMOVE=Remove Files?(y/n)
IF /I %REMOVE% NEQ y GOTO end
rmdir /s /q %charaid%
del /q %charaid%.mdl
del /q %charaid%.mdl.bak
del /q %charaid%.mdl.original_encrypted
echo Process finished
GOTO end

:inited92cle
set gamebase=%gamebase%THE LEGEND OF HEROES KURO NO KISEKI2
set gamemdlfolder="%gamebase%\c\asset\common\model
set gameimgfolder="%gamebase%\c\asset\dx11\image
set extract_prefix=model_kuro2_cle
IF NOT EXIST "%gamebase%\ed9.exe" GOTO wrongpath
echo ED92 云豹版
GOTO endofsetting

:inited93cle
set gamebase=%gamebase%The Legend of Heroes Kai no Kiseki -Farewell, O Zemuria-
set gamemdlfolder="%gamebase%\asset\common\model
set gameimgfolder="%gamebase%\asset\dx11\image
set extract_prefix=model_kai_cle
IF NOT EXIST "%gamebase%\ed9.exe" GOTO wrongpath
echo ED93 云豹版
GOTO endofsetting

:initsora1cle
set gamebase=%gamebase%Sora No Kiseki the 1st
set gamemdlfolder="%gamebase%\pac\steam\asset\common\model
set gameimgfolder="%gamebase%\pac\steam\asset\dx11\image
set extract_prefix=model_sora1_cle
IF NOT EXIST "%gamebase%\sora_1st.exe" GOTO wrongpath
echo sora1 云豹版
GOTO endofsetting

:initys10cle
set gamebase=%gamebase%Ys X -NORDICS-
set gamemdlfolder="%gamebase%\asset\common\model
set gameimgfolder="%gamebase%\asset\dx11\image
set extract_prefix=model_ys10_cle
IF NOT EXIST "%gamebase%\ysx.exe" GOTO wrongpath
echo Ys10 云豹版
GOTO endofsetting

:initys10pcle
set gamebase=%gamebase%Ys X -Proud NORDICS-
set gamemdlfolder="%gamebase%\asset\common\model
set gameimgfolder="%gamebase%\asset\dx11\image
set extract_prefix=model_ys10p_cle
IF NOT EXIST "%gamebase%\ysx.exe" GOTO wrongpath
echo Ys10P 云豹版
GOTO endofsetting

:initys10nisa
set gamebase=%gamebase%YS X Nordics
set gamemdlfolder="%gamebase%\asset\common\model
set gameimgfolder="%gamebase%\asset\dx11\image
set extract_prefix=model_ys10_nisa
IF NOT EXIST "%gamebase%\ysx.exe" GOTO wrongpath
echo YS10 NISA版 请注意先解包p3a资源
GOTO endofsetting

:wrongpath
echo please modify gamebase first
echo current: %gamebase%
GOTO end

:printhelp
echo param1 not avaliable: '%1'
echo avaliable values: ed92cle,ed93cle,ys10cle,ys10pcle,ys10nisa,sora1cle
echo param2: inject/other
echo param3: keepfiles/other
goto end

:end
pause