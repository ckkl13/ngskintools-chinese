@echo off
REM 设置文件夹路径
set "folder_path=C:\ProgramData\Autodesk\ApplicationPlugins\ngskintools2"

REM 检查是否存在
if exist "%folder_path%" (
    REM 删除所有内容
    rd /s /q "%folder_path%"
    if errorlevel 1 (
        echo 删除失败！请检查权限或文件夹状态!
    ) else (
        echo 卸载成功！
    )
) else (
    echo Ngskintools不存在!
)

pause