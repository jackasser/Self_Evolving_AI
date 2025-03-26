#!/usr/bin/env python3
"""
自律的AIシステム 起動スクリプト

自律的に学習、目標設定、情報収集を行うAIシステムを起動します。
"""

import os
import sys
import logging
import json
import argparse
import time
from datetime import datetime

# Windows環境での文字コード問題に対応
if sys.platform == 'win32':
    import locale
    sys_enc = locale.getpreferredencoding()
    if sys_enc != 'utf-8':
        # stdoutをutf-8でリコンフィグ
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')

from autonomous_ai import AutonomousAI

def setup_logging(debug=False):
    """ロギングの設定"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("autonomous_ai.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("main")

def clear_screen():
    """画面クリア"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """ヘッダー表示"""
    print("=" * 80)
    print("  自律的 AI システム  ".center(80))
    print("=" * 80)
    print("\n自律的に学習し、知識を蓄積し、目標を達成するAIアシスタント")
    print("Type 'exit' or 'quit' to end the session.")
    print("Special commands:")
    print("  /status  - システム状態を表示")
    print("  /goals   - 目標一覧を表示")
    print("  /auto    - 自律モードの切り替え")
    print("  /learn   - 直近のクエリについて学習を実行")
    print("  /search:クエリ - Web検索を実行")
    print("  /think   - 思考プロセスを表示")
    print("  /cycle   - 自律サイクルを実行")
    print("  /help    - コマンド一覧を表示\n")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="自律的AIシステム")
    parser.add_argument("--config", default="config.json", help="設定ファイルへのパス")
    parser.add_argument("--debug", action="store_true", help="デバッグモードを有効化")
    parser.add_argument("--no-auto", action="store_true", help="自律モードを無効化して起動")
    args = parser.parse_args()
    
    # ロギングの設定
    logger = setup_logging(args.debug)
    logger.info("Starting Autonomous AI System...")
    
    try:
        # 設定ファイルの読み込み
        try:
            with open(args.config, "r", encoding='utf-8') as f:
                config = json.load(f)
                
            # 自律モードの設定を更新（コマンドライン引数が優先）
            if args.no_auto:
                config["autonomous_mode"] = False
                
            # 設定ファイルに書き戻し
            with open(args.config, "w", encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to load/update config: {str(e)}")
            # デフォルト設定を作成
            config = {
                "autonomous_mode": not args.no_auto,
                "autonomous_interval_seconds": 300,
                "state_save_interval_seconds": 600
            }
            
            # 新しい設定ファイルを作成
            with open(args.config, "w", encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 自律AIの初期化
        ai = AutonomousAI(config_path=args.config)
        
        # AIの起動
        ai.start()
        
        # メインインタラクションループ
        clear_screen()
        print_header()
        
        session_active = True
        while session_active:
            # ユーザー入力を取得
            user_input = input("\nあなた > ")
            
            # 終了コマンドのチェック
            if user_input.lower() in ["exit", "quit"]:
                print("\nシステムを終了します。ご利用ありがとうございました。")
                ai.stop()
                session_active = False
                continue
            
            # 入力処理
            try:
                start_time = time.time()
                response = ai.process_input(user_input)
                processing_time = time.time() - start_time
                
                print(f"\nAI > {response}")
                
                if args.debug:
                    print(f"\n[処理時間: {processing_time:.2f}秒]")
                    
            except Exception as e:
                logger.error(f"処理エラー: {str(e)}", exc_info=True)
                print("\nAI > 処理中にエラーが発生しました。もう一度お試しください。")
                if args.debug:
                    print(f"エラー詳細: {str(e)}")
    
    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました。")
        try:
            ai.stop()
        except:
            pass
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\nエラーが発生しました: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
    
    logger.info("Autonomous AI System shutdown")
    return 0

if __name__ == "__main__":
    main()
