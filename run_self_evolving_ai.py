import os
import sys
import logging
import json
import argparse
from datetime import datetime

from self_evolving_ai import SelfEvolvingAI

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("self_evolving_ai.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("run_script")

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header."""
    print("=" * 80)
    print("  自己成長型AI (Self-Evolving AI)  ".center(80))
    print("=" * 80)
    print("\n独自に学習し、知識を蓄積し、自己最適化を行うAIアシスタント")
    print("Type 'exit' or 'quit' to end the session.")
    print("Special commands:")
    print("  /status  - システム状態を表示")
    print("  /evolve  - 進化サイクルを実行")
    print("  /help    - コマンド一覧を表示")
    print("  /search:query - Webから情報を検索 (例: /search:人工知能)\n")

def show_system_status(ai):
    """Display system status"""
    status = ai.get_system_status()
    
    print("\n" + "=" * 50)
    print("システム状態".center(50))
    print("=" * 50)
    
    # 基本情報
    print(f"\n基本情報:")
    print(f"  状態: {status['system_state']['status']}")
    print(f"  開始時刻: {status['system_state']['started_at']}")
    print(f"  実行時間: {status['uptime_seconds']:.1f}秒")
    print(f"  進化サイクル: {status['evolution_cycles_completed']}回")
    
    # 健全性情報
    print(f"\n健全性情報:")
    print(f"  健全性スコア: {status['health']['health_score']}")
    print(f"  状態: {status['health']['status']}")
    print(f"  エラーコンポーネント: {len(status['health']['error_components'])}")
    
    # リソース情報
    print(f"\nリソース情報:")
    print(f"  メモリ使用率: {status['resources']['system']['memory_usage_percent']}%")
    print(f"  CPU使用率: {status['resources']['system']['cpu_usage_percent']}%")
    
    # 目標と最適化
    print(f"\n目標と最適化:")
    print(f"  アクティブな目標: {status['active_goals']}個")
    print(f"  アクティブな最適化: {status['active_optimizations']}個")
    print(f"  完了した目標: {status['system_state']['goals_completed']}個")
    
    # 知識ベース情報
    kb_stats = ai.get_knowledge_stats()
    print(f"\n知識ベース:")
    print(f"  事実: {kb_stats['facts_count']}項目")
    print(f"  概念: {kb_stats['concepts_count']}項目")
    print(f"  方法: {kb_stats['methods_count']}項目")
    print(f"  関係: {kb_stats['relations_count']}項目")
    print(f"  合計: {kb_stats['total_items']}項目")
    
    print("\n" + "=" * 50)

def run_evolution_cycle(ai):
    """Run an evolution cycle"""
    print("\n進化サイクルを実行中...")
    start_time = datetime.now()
    
    try:
        result = ai.run_evolution_cycle()
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n進化サイクル完了 ({duration:.2f}秒)")
        print(f"新しい目標: {result['goals']['new_goals_set']}個設定")
        print(f"目標更新: {result['goals']['goals_updated']}個更新")
        print(f"最適化実装: {result['optimizations']['optimizations_implemented']}個")
        print(f"最適化完了: {result['optimizations']['optimizations_completed']}個")
        print(f"知識拡張: {result['knowledge']['successful_expansions']}件")
        
    except Exception as e:
        print(f"\n進化サイクルの実行中にエラーが発生しました: {str(e)}")

def show_help():
    """Show help information"""
    print("\n" + "=" * 50)
    print("コマンド一覧".center(50))
    print("=" * 50)
    print("\n一般的な会話: 通常の文章を入力すると、AIが応答します")
    print("\n特殊コマンド:")
    print("  /status  - システムの現在の状態を表示")
    print("  /evolve  - 進化サイクルを手動で実行")
    print("  /help    - このヘルプメッセージを表示")
    print("  /search:クエリ - 指定したクエリでWeb検索を実行")
    print("  /exit または quit - プログラムを終了")
    print("\n" + "=" * 50)

def main():
    """Main function to run the Self-Evolving AI"""
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(description="Self-Evolving AI System")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Windowsの場合は文字コード対応
    if sys.platform == 'win32':
        import locale
        sys_enc = locale.getpreferredencoding()
        # UTF-8をデフォルトエンコーディングとして設定
        if sys_enc != 'utf-8':
            # stdoutをutf-8でリコンフィグ
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
    
    try:
        # 自己成長型AIの初期化
        ai = SelfEvolvingAI(config_path=args.config)
        
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
            
            # 特殊コマンドのチェック
            if user_input.startswith("/"):
                if user_input.lower() == "/status":
                    show_system_status(ai)
                    continue
                    
                elif user_input.lower() == "/evolve":
                    run_evolution_cycle(ai)
                    continue
                    
                elif user_input.lower() == "/help":
                    show_help()
                    continue
                    
                # 検索コマンドの処理
                elif user_input.lower().startswith("/search:"):
                    query = user_input[8:].strip()
                    if query:
                        print(f"\n「{query}」について検索しています...")
                        response = ai.search_web_knowledge(query)
                        
                        if response["status"] == "success":
                            items = response.get("knowledge_items", [])
                            print(f"\n{len(items)}件の情報が見つかりました。")
                            
                            for i, item in enumerate(items[:5], 1):
                                print(f"\n{i}. {item.get('content')}")
                                
                            if len(items) > 5:
                                print(f"\n...他{len(items)-5}件の情報があります。")
                        else:
                            print(f"\n検索エラー: {response.get('error', '情報が見つかりませんでした')}")
                    else:
                        print("\n検索クエリを入力してください。例: /search:人工知能")
                    continue
            
            # 通常の入力処理
            try:
                response = ai.process_input(user_input)
                print(f"\nAI > {response}")
            except Exception as e:
                if args.debug:
                    logger.error(f"エラー: {str(e)}", exc_info=True)
                    print(f"\nエラー: {str(e)}")
                else:
                    print("\nAI > リクエストの処理中に問題が発生しました。もう一度試してください。")
    
    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました。")
        if 'ai' in locals():
            ai.stop()
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        print(f"\nエラーが発生しました: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
    
    return 0

if __name__ == "__main__":
    main()
