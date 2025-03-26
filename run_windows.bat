@echo off
REM 自己成長型AI用のWindows実行スクリプト
REM エンコーディングの問題を解決するために環境変数を設定

set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
chcp 65001 > NUL

echo 自己成長型AI (Self-Evolving AI) を起動中...

REM 専用スクリプトで自己成長型AIを起動
python run_self_evolving_ai.py --config config.json

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 実行中にエラーが発生しました。何かキーを押して終了してください。
    pause > nul
) else (
    echo.
    echo 自己成長型AIを終了しました。何かキーを押して終了してください。
    pause > nul
)
