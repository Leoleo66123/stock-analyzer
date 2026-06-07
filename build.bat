@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   股票智能分析系统 - 一键打包
echo ============================================
echo.
echo [1/3] 清理旧构建...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
echo [2/3] PyInstaller 打包中 (约 3-8 分钟)...
pyinstaller build.spec --clean --noconfirm
echo.
if exist "dist\StockAnalyzer.exe" (
    echo [3/3] 打包成功！
    echo.
    echo 成品位置: %CD%\dist\StockAnalyzer.exe
    explorer /select,"%CD%\dist\StockAnalyzer.exe"
) else (
    echo [失败] 打包出错，检查上方日志。
)
echo.
pause