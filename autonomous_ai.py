"""
自律AIシステム

自律的に学習、思考、目標設定できるAIシステムのメインモジュール。
すべてのコンポーネントを統合し、調整する中央コントローラ。
"""

import logging
import json
import time
import os
import threading
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# コンポーネントのインポート
from knowledge_base import KnowledgeBase
from web_searcher import WebSearcher
from autonomous_learning import AutonomousLearning
from goal_system import GoalSystem
from thinking_engine import ThinkingEngine

class AutonomousAI:
    """
    自律的なAIシステムのメインクラス
    すべてのコンポーネントを統合し、自律的な動作を管理する
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        AutonomousAIの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # ロギングの設定
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("autonomous_ai.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("autonomous_ai")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            self.config = {}
        
        # システム状態
        self.system_state = {
            "status": "initializing",
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "processing_count": 0,
            "autonomous_mode": self.config.get("autonomous_mode", True)
        }
        
        # コンポーネントの初期化
        self.logger.info("Initializing autonomous AI components...")
        
        # 知識ベース
        self.knowledge_base = KnowledgeBase(config_path=config_path)
        
        # Web検索
        self.web_searcher = WebSearcher(config_path=config_path)
        
        # 自律学習
        self.learning = AutonomousLearning(
            kb=self.knowledge_base,
            web_searcher=self.web_searcher,
            config_path=config_path
        )
        
        # 目標システム
        self.goal_system = GoalSystem(config_path=config_path)
        
        # 思考エンジン
        self.thinking_engine = ThinkingEngine(config_path=config_path)
        
        # 会話コンテキスト
        self.conversation_context = {
            "history": [],
            "current_topic": None,
            "user_preferences": {},
            "last_queries": []
        }
        
        # 自律活動スレッド
        self.autonomous_thread = None
        self.autonomous_active = False
        
        # 自律モードの期間（秒）
        self.autonomous_interval = self.config.get("autonomous_interval_seconds", 300)  # デフォルト5分
        
        # 状態保存間隔（秒）
        self.state_save_interval = self.config.get("state_save_interval_seconds", 600)  # デフォルト10分
        self.last_state_save = time.time()
        
        # 保存ディレクトリ
        self.save_dir = "autonomous_ai_data"
        os.makedirs(self.save_dir, exist_ok=True)
        
        self.logger.info("Autonomous AI initialized")
    
    def start(self) -> bool:
        """
        自律AIを起動
        
        Returns:
            起動が成功したかどうか
        """
        self.logger.info("Starting Autonomous AI...")
        
        # システム状態を更新
        self.system_state["status"] = "active"
        
        # 自律モードが有効なら自律スレッドを開始
        if self.system_state["autonomous_mode"]:
            self.autonomous_active = True
            self.autonomous_thread = threading.Thread(
                target=self._autonomous_loop,
                daemon=True
            )
            self.autonomous_thread.start()
            self.logger.info("Autonomous mode activated")
        
        self.logger.info("Autonomous AI started successfully")
        return True
    
    def stop(self) -> bool:
        """
        自律AIを停止
        
        Returns:
            停止が成功したかどうか
        """
        self.logger.info("Stopping Autonomous AI...")
        
        # 自律スレッドを停止
        if self.autonomous_active:
            self.autonomous_active = False
            if self.autonomous_thread and self.autonomous_thread.is_alive():
                self.autonomous_thread.join(timeout=10.0)
        
        # 状態を保存
        self._save_state()
        
        # システム状態を更新
        self.system_state["status"] = "stopped"
        
        self.logger.info("Autonomous AI stopped successfully")
        return True
    
    def process_input(self, user_input: str) -> str:
        """
        ユーザー入力を処理し、応答を生成
        
        Args:
            user_input: ユーザーの入力テキスト
            
        Returns:
            AIの応答
        """
        start_time = time.time()
        self.system_state["processing_count"] += 1
        self.system_state["last_activity"] = datetime.now().isoformat()
        
        self.logger.info(f"Processing user input: {user_input[:50]}...")
        
        # 入力をコンテキストに追加
        self.conversation_context["history"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 最近のクエリに追加
        self.conversation_context["last_queries"].append(user_input)
        if len(self.conversation_context["last_queries"]) > 5:
            self.conversation_context["last_queries"] = self.conversation_context["last_queries"][-5:]
        
        # 特殊コマンドの処理
        if user_input.startswith("/"):
            response = self._handle_command(user_input)
            
            # レスポンスをコンテキストに追加
            self.conversation_context["history"].append({
                "role": "ai",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
        
        # 1. 入力の理解と分析（思考エンジンを使用）
        understanding = self.thinking_engine.think(
            query=user_input,
            context={"conversation_history": self.conversation_context["history"][-10:]},
            mode="analytical",
            depth=1  # クイック分析
        )
        
        # 2. 知識ギャップの特定
        knowledge_gaps = self.learning.identify_knowledge_gaps(user_input, self.conversation_context)
        
        # 3. 必要に応じて知識を獲得
        acquired_knowledge = []
        if knowledge_gaps:
            for gap in knowledge_gaps[:1]:  # 最も重要なギャップのみ対応
                # 学習計画を作成
                learning_plan = self.learning.create_learning_plan(gap)
                
                # 学習計画を実行（バックグラウンドで実行するため簡易化）
                if self.system_state["autonomous_mode"]:
                    # 非同期実行（本来はスレッドプールなどを使用）
                    # ここでは簡略化のため単一トピックのみ検索
                    search_results = self.web_searcher.search(gap["topic"], max_results=3)
                    if search_results.get("status") in ["success", "partial_success"]:
                        for result in search_results.get("results", [])[:1]:
                            # 詳細コンテンツを取得
                            detailed_content = self.web_searcher.get_article_content(result["url"])
                            if detailed_content.get("status") == "success":
                                # 知識ベースに保存
                                fact_id = self.knowledge_base.store_fact(
                                    content=detailed_content.get("content", "")[:500],  # 長すぎる場合は切り詰め
                                    source=result["url"],
                                    confidence=0.7
                                )
                                if fact_id > 0:
                                    acquired_knowledge.append({
                                        "topic": gap["topic"],
                                        "content": detailed_content.get("title", "") + "\n" + detailed_content.get("content", "")[:100] + "..."
                                    })
        
        # 4. 応答生成
        # 関連知識を検索
        relevant_knowledge = self.knowledge_base.search_knowledge(user_input, limit=5)
        
        # 思考エンジンによる応答生成
        thinking_context = {
            "conversation_history": self.conversation_context["history"][-5:],
            "relevant_knowledge": relevant_knowledge,
            "acquired_knowledge": acquired_knowledge
        }
        
        thinking_result = self.thinking_engine.think(
            query=f"ユーザーの質問「{user_input}」への応答を生成",
            context=thinking_context,
            mode="analytical",
            depth=2  # 詳細な分析
        )
        
        # 結論から応答を抽出
        response = thinking_result.get("conclusion", "")
        
        # 応答が生成されなかった場合のフォールバック
        if not response or len(response) < 20:
            # 関連知識があれば、それを基に応答
            if relevant_knowledge["total_results"] > 0:
                knowledge_texts = []
                
                # 事実から情報を収集
                for fact in relevant_knowledge.get("facts", [])[:2]:
                    knowledge_texts.append(fact.get("content", ""))
                
                # 概念から情報を収集
                for concept in relevant_knowledge.get("concepts", [])[:2]:
                    if concept.get("definitions"):
                        for definition in concept.get("definitions", [])[:2]:
                            if isinstance(definition, dict) and "content" in definition:
                                knowledge_texts.append(definition.get("content", ""))
                
                # 関連知識に基づく応答を生成
                if knowledge_texts:
                    response = f"「{user_input}」についてお答えします。\n\n"
                    response += "\n\n".join(knowledge_texts)
                else:
                    response = f"「{user_input}」について詳しい情報を持っていませんが、関連する情報を探してみます。"
            else:
                # 知識がない場合の汎用応答
                response = f"「{user_input}」について詳しい情報を持っていません。別の質問をしていただくか、より具体的な情報をご提供いただければ、お役に立てるかもしれません。"
            
            # 新たに獲得した知識がある場合は追加
            if acquired_knowledge:
                response += "\n\n以下は今回新たに学んだ情報です：\n"
                for item in acquired_knowledge:
                    response += f"\n- {item['topic']}に関して: {item['content'][:100]}..."
        
        # レスポンスをコンテキストに追加
        self.conversation_context["history"].append({
            "role": "ai",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 処理時間のログを記録
        processing_time = time.time() - start_time
        self.logger.info(f"Processed input in {processing_time:.2f} seconds")
        
        # 必要に応じて状態を保存
        if time.time() - self.last_state_save >= self.state_save_interval:
            self._save_state()
        
        return response
    
    def search_web(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            検索結果
        """
        self.logger.info(f"Searching web for: {query}")
        self.system_state["last_activity"] = datetime.now().isoformat()
        
        # Web検索の実行
        search_results = self.web_searcher.search(query, max_results=max_results)
        
        # 検索結果を会話コンテキストに追加
        self.conversation_context["history"].append({
            "role": "system",
            "content": f"Web検索: {query}",
            "search_results": search_results.get("results", []),
            "timestamp": datetime.now().isoformat()
        })
        
        return search_results
    
    def set_autonomous_mode(self, enabled: bool) -> Dict[str, Any]:
        """
        自律モードの有効/無効を設定
        
        Args:
            enabled: 自律モードを有効にするかどうか
            
        Returns:
            設定結果
        """
        previous_state = self.system_state["autonomous_mode"]
        self.system_state["autonomous_mode"] = enabled
        
        if enabled and not previous_state:
            # 自律モードを有効化
            if not self.autonomous_active:
                self.autonomous_active = True
                self.autonomous_thread = threading.Thread(
                    target=self._autonomous_loop,
                    daemon=True
                )
                self.autonomous_thread.start()
                self.logger.info("Autonomous mode activated")
        elif not enabled and previous_state:
            # 自律モードを無効化
            self.autonomous_active = False
            if self.autonomous_thread and self.autonomous_thread.is_alive():
                self.autonomous_thread.join(timeout=10.0)
                self.logger.info("Autonomous mode deactivated")
        
        return {
            "status": "success",
            "autonomous_mode": self.system_state["autonomous_mode"],
            "previous_state": previous_state
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        システムの現在の状態を取得
        
        Returns:
            システム状態の情報
        """
        # 知識ベースの統計
        kb_stats = self.knowledge_base.get_knowledge_stats()
        
        # Web検索の統計
        web_stats = self.web_searcher.get_search_stats()
        
        # 学習の統計
        learning_stats = self.learning.get_learning_stats()
        
        # 目標の統計
        goal_stats = self.goal_system.get_goal_stats()
        
        # 思考エンジンの統計
        thinking_stats = self.thinking_engine.get_thinking_stats()
        
        # システム稼働時間
        started_at = datetime.fromisoformat(self.system_state["started_at"])
        uptime_seconds = (datetime.now() - started_at).total_seconds()
        
        # ステータスデータの作成
        status = {
            "timestamp": datetime.now().isoformat(),
            "system_state": self.system_state,
            "uptime_seconds": uptime_seconds,
            "knowledge_base": kb_stats,
            "web_search": web_stats,
            "learning": learning_stats,
            "goals": goal_stats,
            "thinking": thinking_stats,
            "conversation": {
                "history_length": len(self.conversation_context["history"]),
                "last_interaction": self.conversation_context["history"][-1]["timestamp"] if self.conversation_context["history"] else None
            }
        }
        
        return status
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        現在のアクティブな目標を取得
        
        Returns:
            アクティブな目標のリスト
        """
        return self.goal_system.get_active_goals()
    
    def run_autonomous_cycle(self) -> Dict[str, Any]:
        """
        自律サイクルを手動で実行
        
        Returns:
            実行結果
        """
        self.logger.info("Manually running autonomous cycle")
        
        results = self._run_autonomous_activities()
        
        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_command(self, command: str) -> str:
        """特殊コマンドの処理"""
        cmd_lower = command.lower()
        
        if cmd_lower == "/status":
            # システム状態の表示
            status = self.get_system_status()
            
            response = "=== システム状態 ===\n\n"
            response += f"状態: {status['system_state']['status']}\n"
            response += f"自律モード: {'有効' if status['system_state']['autonomous_mode'] else '無効'}\n"
            response += f"実行時間: {status['uptime_seconds']:.1f}秒\n\n"
            
            response += "=== 知識ベース ===\n"
            response += f"事実: {status['knowledge_base']['facts_count']} 項目\n"
            response += f"概念: {status['knowledge_base']['concepts_count']} 項目\n"
            response += f"関係: {status['knowledge_base']['relations_count']} 項目\n\n"
            
            response += "=== 目標 ===\n"
            response += f"アクティブな目標: {status['goals']['active_goals']} 個\n"
            response += f"完了した目標: {status['goals']['completed_goals']} 個\n\n"
            
            response += "=== 学習 ===\n"
            response += f"学習計画: {status['learning']['total_learning_plans']} 個\n"
            response += f"獲得知識: {status['learning']['total_knowledge_acquired']} 項目\n\n"
            
            response += "=== Web検索 ===\n"
            response += f"総検索回数: {status['web_search'].get('total_searches', 0)} 回\n"
            
            return response
            
        elif cmd_lower == "/goals":
            # 目標一覧の表示
            goals = self.get_active_goals()
            
            if not goals:
                return "現在アクティブな目標はありません。"
            
            response = "=== アクティブな目標 ===\n\n"
            for i, goal in enumerate(goals, 1):
                response += f"{i}. {goal['description']}\n"
                response += f"   進捗: {goal['progress']}%\n"
                response += f"   優先度: {goal['priority']}\n"
                response += f"   タイプ: {goal['type']}\n\n"
            
            return response
            
        elif cmd_lower == "/autonomous" or cmd_lower == "/auto":
            # 自律モードの切り替え
            current_mode = self.system_state["autonomous_mode"]
            result = self.set_autonomous_mode(not current_mode)
            
            return f"自律モードを{'有効' if result['autonomous_mode'] else '無効'}にしました。"
            
        elif cmd_lower == "/learn":
            # 学習サイクルの実行
            if not self.conversation_context["last_queries"]:
                return "学習するクエリがありません。何か質問をしてから再試行してください。"
            
            # 直近のクエリについて学習
            last_query = self.conversation_context["last_queries"][-1]
            gaps = self.learning.identify_knowledge_gaps(last_query)
            
            if not gaps:
                return f"「{last_query}」に関する知識ギャップは見つかりませんでした。"
            
            # 最初のギャップについて学習
            gap = gaps[0]
            plan = self.learning.create_learning_plan(gap)
            
            # 非同期実行が理想だが、ここでは同期実行
            results = self.learning.execute_learning_plan(plan["id"])
            
            return f"「{gap['topic']}」についての学習を完了しました。{results['knowledge_acquired']}項目の新しい知識を獲得しました。"
            
        elif cmd_lower.startswith("/search:"):
            # Web検索
            query = command[8:].strip()
            if not query:
                return "検索クエリを指定してください。例: /search:人工知能"
            
            search_results = self.search_web(query)
            
            if search_results.get("status") in ["success", "partial_success"]:
                results = search_results.get("results", [])
                
                if not results:
                    return f"「{query}」に関する検索結果が見つかりませんでした。"
                
                response = f"「{query}」の検索結果：\n\n"
                
                for i, result in enumerate(results[:5], 1):
                    response += f"{i}. {result.get('title', '不明なタイトル')}\n"
                    response += f"   {result.get('content', '')[:100]}...\n\n"
                
                if len(results) > 5:
                    response += f"...他 {len(results) - 5} 件の結果があります。"
                
                return response
            else:
                return f"検索中にエラーが発生しました：{search_results.get('message', '不明なエラー')}"
            
        elif cmd_lower == "/think":
            # 思考プロセスの実行
            if not self.conversation_context["last_queries"]:
                return "思考するクエリがありません。何か質問をしてから再試行してください。"
            
            # 直近のクエリについて思考
            last_query = self.conversation_context["last_queries"][-1]
            
            thinking_result = self.thinking_engine.think(
                query=last_query,
                context={"conversation_history": self.conversation_context["history"][-5:]},
                mode="analytical",
                depth=3  # 最大深度
            )
            
            response = "=== 思考プロセス ===\n\n"
            
            # 思考モードに応じたレスポンス形式
            if "problem" in thinking_result:
                response += f"問題: {thinking_result.get('problem', '')}\n\n"
                response += f"仮説: {thinking_result.get('hypothesis', '')}\n\n"
                response += f"分析: {thinking_result.get('analysis', '')}\n\n"
            
            if "ideas" in thinking_result:
                response += f"アイデア: {thinking_result.get('ideas', '')}\n\n"
            
            response += f"結論: {thinking_result.get('conclusion', '')}\n"
            
            return response
            
        elif cmd_lower == "/cycle" or cmd_lower == "/evolve":
            # 自律サイクルの実行
            result = self.run_autonomous_cycle()
            
            return f"自律サイクルを実行しました。\n\n獲得知識: {result['results'].get('acquired_knowledge', 0)}項目\n目標進捗: {result['results'].get('goals_updated', 0)}個\n新規目標: {result['results'].get('new_goals', 0)}個"
            
        elif cmd_lower == "/help":
            # ヘルプの表示
            response = "=== 使用可能なコマンド ===\n\n"
            response += "/status  - システムの現在の状態を表示\n"
            response += "/goals   - アクティブな目標の一覧を表示\n"
            response += "/auto    - 自律モードの有効/無効を切り替え\n"
            response += "/learn   - 直近のクエリについて学習を実行\n"
            response += "/search:クエリ - 指定したクエリでWeb検索を実行\n"
            response += "/think   - 直近のクエリについて詳細な思考プロセスを実行\n"
            response += "/cycle   - 自律サイクルを手動で実行\n"
            response += "/help    - このヘルプメッセージを表示\n"
            
            return response
            
        else:
            # 不明なコマンド
            return f"不明なコマンドです: {command}\n利用可能なコマンドのリストを見るには /help と入力してください。"
    
    def _autonomous_loop(self) -> None:
        """自律行動ループ"""
        self.logger.info("Autonomous loop started")
        
        while self.autonomous_active:
            try:
                # 一定間隔で自律的な活動を実行
                self._run_autonomous_activities()
                
                # 状態保存
                if time.time() - self.last_state_save >= self.state_save_interval:
                    self._save_state()
                
                # 次のサイクルまで待機
                time.sleep(self.autonomous_interval)
                
            except Exception as e:
                self.logger.error(f"Error in autonomous loop: {str(e)}")
                time.sleep(60)  # エラー後は少し待機
    
    def _run_autonomous_activities(self) -> Dict[str, Any]:
        """自律的な活動の実行"""
        self.logger.info("Running autonomous activities")
        
        results = {
            "cycle_start": datetime.now().isoformat(),
            "acquired_knowledge": 0,
            "goals_updated": 0,
            "new_goals": 0
        }
        
        try:
            # 1. 目標レビュー
            goal_review = self.goal_system.review_goals()
            if goal_review.get("status") == "success":
                results["goals_updated"] = goal_review["results"]["reviewed_goals"]
                results["new_goals"] = goal_review["results"]["goals_suggested"]
            
            # 2. 学習活動
            # 次のタスクを取得
            next_task = self.goal_system.get_next_task()
            if next_task:
                # 学習ギャップを特定
                gaps = self.learning.identify_knowledge_gaps(next_task["description"])
                
                if gaps:
                    # 最も重要なギャップについて学習
                    gap = gaps[0]
                    plan = self.learning.create_learning_plan(gap)
                    
                    # 学習計画を実行
                    learning_results = self.learning.execute_learning_plan(plan["id"])
                    
                    # 知識獲得数を記録
                    results["acquired_knowledge"] = learning_results["knowledge_acquired"]
                    
                    # タスク進捗を更新
                    self.goal_system.update_progress(
                        goal_id=next_task["goal_id"],
                        progress=50,  # 仮の進捗値
                        completed_subtasks=[next_task["subtask_id"]]
                    )
            
            # 3. アイデア生成と目標提案
            if random.random() < 0.3:  # 30%の確率でアイデア生成
                # 既存の知識をランダムに選択
                kb_stats = self.knowledge_base.get_knowledge_stats()
                if kb_stats["facts_count"] > 0:
                    random_query = "知識拡張"
                    
                    # 思考エンジンを使用してアイデア生成
                    ideas = self.thinking_engine.generate_ideas(
                        challenge=f"「{random_query}」に関する知識をさらに拡充するための方法",
                        count=2
                    )
                    
                    # アイデアを目標に変換
                    for idea in ideas.get("ideas", [])[:1]:  # 最初のアイデアのみ
                        self.goal_system.set_goal(
                            description=idea["description"],
                            goal_type="knowledge_acquisition",
                            priority=3
                        )
                        results["new_goals"] += 1
            
            results["cycle_end"] = datetime.now().isoformat()
            self.logger.info(f"Autonomous activities completed: {results}")
            
        except Exception as e:
            self.logger.error(f"Error during autonomous activities: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _save_state(self) -> None:
        """システムの状態を保存"""
        try:
            # 保存ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.save_dir, f"ai_state_{timestamp}.json")
            
            # 保存データの準備
            save_data = {
                "system_state": self.system_state,
                "conversation_context": {
                    "history_length": len(self.conversation_context["history"]),
                    "current_topic": self.conversation_context["current_topic"],
                    "last_queries": self.conversation_context["last_queries"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.last_state_save = time.time()
            self.logger.info(f"System state saved to {filename}")
            
            # 古いファイルを削除（最新10件を保持）
            self._cleanup_old_files()
            
        except Exception as e:
            self.logger.error(f"Error saving system state: {str(e)}")
    
    def _cleanup_old_files(self) -> None:
        """古い状態ファイルを削除"""
        files = [os.path.join(self.save_dir, f) for f in os.listdir(self.save_dir) 
                if f.startswith("ai_state_") and f.endswith(".json")]
        
        # 更新日時でソート（新しい順）
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        # 最新の10件を残して削除
        for file_to_delete in files[10:]:
            try:
                os.remove(file_to_delete)
            except Exception as e:
                self.logger.warning(f"Failed to delete old file {file_to_delete}: {str(e)}")
