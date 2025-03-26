#!/bin/bash
# 自己成長型AI用の実行スクリプト（Linux/macOS用）

# エンコーディング設定
export PYTHONIOENCODING=utf-8

echo "自己成長型AI (Self-Evolving AI) を起動中..."

# 自己成長型AI専用スクリプトで起動
python run_self_evolving_ai.py --config config.json

# 終了ステータスの確認
if [ $? -ne 0 ]; then
    echo "実行中にエラーが発生しました。"
    echo "Enterキーを押して終了してください。"
    read
else
    echo "自己成長型AIを終了しました。"
    echo "Enterキーを押して終了してください。"
    read
fi
