@echo off
REM �����ļ���·��
set "folder_path=C:\ProgramData\Autodesk\ApplicationPlugins\ngskintools2"

REM ����Ƿ����
if exist "%folder_path%" (
    REM ɾ����������
    rd /s /q "%folder_path%"
    if errorlevel 1 (
        echo ɾ��ʧ�ܣ�����Ȩ�޻��ļ���״̬!
    ) else (
        echo ж�سɹ���
    )
) else (
    echo Ngskintools������!
)

pause