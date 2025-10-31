@echo off
echo Deleted .pyc files:
for /r %%a in (".\*") do (
	if "%%~xa" EQU ".pyc" (
		echo %%a
		del %%a
	)
)
echo Deleted __pycache__ directories:
for /r /d %%d in (".\*") do (
	if "%%~nd" EQU "__pycache__" (
		echo %%d
		rmdir %%d
	)
)
pause