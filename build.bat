@echo off
echo ======================================
echo    打包 Cursor Helper 可执行文件
echo ======================================
echo.

:: 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装Python或Python不在PATH中
    goto :error
)

:: 安装必要的依赖
echo [步骤 1] 安装必要的依赖...
python -m pip install pyinstaller pywin32
if errorlevel 1 (
    echo [错误] 安装依赖失败
    goto :error
)

:: 执行打包脚本
echo [步骤 2] 执行打包脚本...
python build.py
if errorlevel 1 (
    echo [错误] 执行打包脚本失败
    goto :error
)

echo.
echo 打包完成！可执行文件在 dist 目录中
echo.
pause
exit /b 0

:error
echo.
echo 打包过程中出现错误，请查看上方日志
pause
exit /b 1 