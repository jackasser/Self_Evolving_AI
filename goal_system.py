"""
目標管理システム

自律的な目標の設定、分解、追跡を行うシステム。
AIが自己設定した目標に向かって行動するための中核機能。
"""

import logging
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class GoalSystem:
    """
    AIの自律的な目標管理を行うクラス
    目標の設定、分解、優先順位付け、追跡を担当
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        GoalSystemの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        self.logger = logging.getLogger("goal_system")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                self.config = config.get("goals", {})
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {}
        
        # 目標一覧
        self.goals = []
        
        # 完了した目標
        self.completed_goals = []
        
        # 目標タイプと優先度の定義
        self.goal_types = {
            "knowledge_acquisition": "新しい知識や情報の獲得",
            "skill_development": "新しいスキルや能力の開発",
            "problem_solving": "特定の問題の解決",
            "creation": "何かを作り出す活動",
            "optimization": "既存のプロセスや機能の最適化",
            "maintenance": "システムの健全性維持",
            "exploration": "新領域の探索",
            "assistance": "ユーザー支援"
        }
        
        self.priority_levels = {
            1: "非常に低い - 時間があれば対応",
            2: "低い - 他に優先すべきことがなければ対応",
            3: "中程度 - 標準的な優先度",
            4: "高い - できるだけ早く対応すべき",
            5: "最高 - 最優先で対応する必要がある"
        }
        
        # データファイル
        self.data_file = self.config.get("data_file", "goals_data.json")
        
        # データのロード
        self._load_data()
        
        # 次の目標レビュー時刻
        self.next_review_time = time.time() + self.config.get("review_interval_hours", 1) * 3600
        
        self.logger.info("Goal system initialized")
    
    def set_goal(self, description: str, goal_type: str = "knowledge_acquisition", 
                priority: int = 3, deadline: Optional[str] = None) -> Dict[str, Any]:
        """
        新しい目標を設定
        
        Args:
            description: 目標の説明
            goal_type: 目標のタイプ
            priority: 優先度 (1-5)
            deadline: 期限 (ISO形式の日時、省略可)
            
        Returns:
            新しい目標のデータ
        """
        # 入力検証
        if not description:
            self.logger.warning("Cannot set goal: empty description")
            return {"status": "error", "message": "Goal description cannot be empty"}
        
        if goal_type not in self.goal_types:
            self.logger.warning(f"Invalid goal type: {goal_type}, using default")
            goal_type = "knowledge_acquisition"
        
        priority = max(1, min(5, priority))  # 1-5の範囲に制限
        
        # 目標IDの生成
        goal_id = f"goal_{int(time.time())}_{len(self.goals)}"
        
        # 目標の作成
        goal = {
            "id": goal_id,
            "description": description,
            "type": goal_type,
            "priority": priority,
            "status": "active",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "deadline": deadline,
            "subtasks": [],
            "dependencies": [],
            "review_count": 0,
            "last_reviewed": None
        }
        
        # 目標の追加
        self.goals.append(goal)
        
        # データの保存
        self._save_data()
        
        self.logger.info(f"Set new goal: {goal_id} - {description}")
        return goal
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        指定IDの目標を取得
        
        Args:
            goal_id: 目標ID
            
        Returns:
            目標データ（見つからない場合はNone）
        """
        for goal in self.goals:
            if goal["id"] == goal_id:
                return goal
        
        # 完了済み目標もチェック
        for goal in self.completed_goals:
            if goal["id"] == goal_id:
                return goal
        
        return None
    
    def decompose_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        """
        目標をサブタスクに分解
        
        Args:
            goal_id: 目標ID
            
        Returns:
            サブタスクのリスト
        """
        goal = self.get_goal(goal_id)
        if not goal:
            self.logger.warning(f"Cannot decompose: goal {goal_id} not found")
            return []
        
        if goal["subtasks"]:
            return goal["subtasks"]  # 既に分解済み
        
        goal_type = goal["type"]
        description = goal["description"]
        
        # 目標タイプに基づくサブタスク生成
        subtasks = []
        
        if goal_type == "knowledge_acquisition":
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」に関する基本情報を調査", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」の主要な概念を理解", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」に関連する実例を確認", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」について知識ベースを更新", "status": "pending", "completed": False}
            ]
        elif goal_type == "skill_development":
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」に必要な基礎知識を獲得", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」の基本手順を学習", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」の練習と実践", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」の評価と改善", "status": "pending", "completed": False}
            ]
        elif goal_type == "problem_solving":
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」問題の詳細分析", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」解決策の複数案検討", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」最適解決策の選択", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」解決策の実行と検証", "status": "pending", "completed": False}
            ]
        elif goal_type == "creation":
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」の要件定義", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」の設計", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」の実装または作成", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」のテストと改善", "status": "pending", "completed": False}
            ]
        elif goal_type == "optimization":
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」の現状分析", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」の改善点特定", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」の最適化実施", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」の最適化効果測定", "status": "pending", "completed": False}
            ]
        else:
            # 汎用的なサブタスク
            subtasks = [
                {"id": f"{goal_id}_sub1", "description": f"「{description}」の調査", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub2", "description": f"「{description}」の計画立案", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub3", "description": f"「{description}」の実行", "status": "pending", "completed": False},
                {"id": f"{goal_id}_sub4", "description": f"「{description}」の評価", "status": "pending", "completed": False}
            ]
        
        # 目標にサブタスクを追加
        goal["subtasks"] = subtasks
        
        # データの保存
        self._save_data()
        
        self.logger.info(f"Decomposed goal {goal_id} into {len(subtasks)} subtasks")
        return subtasks
    
    def update_progress(self, goal_id: str, progress: float, 
                      completed_subtasks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        目標の進捗を更新
        
        Args:
            goal_id: 目標ID
            progress: 進捗度 (0-100)
            completed_subtasks: 完了したサブタスクのIDリスト
            
        Returns:
            更新結果
        """
        goal = self.get_goal(goal_id)
        if not goal:
            self.logger.warning(f"Cannot update progress: goal {goal_id} not found")
            return {"status": "error", "message": "Goal not found"}
        
        # 既に完了している場合
        if goal["status"] == "completed":
            self.logger.warning(f"Cannot update progress: goal {goal_id} already completed")
            return {"status": "error", "message": "Goal already completed"}
        
        # 前回の進捗
        old_progress = goal["progress"]
        
        # 進捗を更新（0-100の範囲に制限）
        goal["progress"] = max(0, min(100, progress))
        
        # 完了したサブタスクを更新
        if completed_subtasks:
            for subtask_id in completed_subtasks:
                for subtask in goal["subtasks"]:
                    if subtask["id"] == subtask_id and not subtask["completed"]:
                        subtask["status"] = "completed"
                        subtask["completed"] = True
                        subtask["completed_at"] = datetime.now().isoformat()
        
        # サブタスクの進捗に基づいて目標の進捗を計算
        if goal["subtasks"]:
            completed_count = sum(1 for st in goal["subtasks"] if st["completed"])
            total_count = len(goal["subtasks"])
            calculated_progress = (completed_count / total_count) * 100 if total_count > 0 else 0
            
            # 手動更新と自動計算の大きい方を採用
            goal["progress"] = max(goal["progress"], calculated_progress)
        
        # 目標の完了チェック
        if goal["progress"] >= 100:
            goal["status"] = "completed"
            goal["completed_at"] = datetime.now().isoformat()
            
            # 完了した目標をリストから移動
            self.goals.remove(goal)
            self.completed_goals.append(goal)
            
            self.logger.info(f"Goal {goal_id} completed")
        
        # 最終更新時刻を更新
        goal["updated_at"] = datetime.now().isoformat()
        
        # データの保存
        self._save_data()
        
        self.logger.info(f"Updated goal {goal_id} progress: {old_progress} -> {goal['progress']}")
        
        return {
            "status": "success",
            "goal_id": goal_id,
            "old_progress": old_progress,
            "new_progress": goal["progress"],
            "completed": goal["status"] == "completed"
        }
    
    def add_dependency(self, goal_id: str, dependency_goal_id: str) -> bool:
        """
        目標間の依存関係を追加
        
        Args:
            goal_id: 依存側の目標ID
            dependency_goal_id: 先行する必要がある目標ID
            
        Returns:
            追加が成功したかどうか
        """
        # 両方の目標が存在するか確認
        goal = self.get_goal(goal_id)
        dependency = self.get_goal(dependency_goal_id)
        
        if not goal or not dependency:
            self.logger.warning(f"Cannot add dependency: one or both goals not found")
            return False
        
        # 循環依存をチェック
        if self._has_circular_dependency(dependency_goal_id, goal_id):
            self.logger.warning(f"Cannot add dependency: would create circular dependency")
            return False
        
        # 依存関係が既に存在するか確認
        if dependency_goal_id in goal["dependencies"]:
            return True  # 既に存在する場合は成功とみなす
        
        # 依存関係を追加
        goal["dependencies"].append(dependency_goal_id)
        
        # データの保存
        self._save_data()
        
        self.logger.info(f"Added dependency: {goal_id} depends on {dependency_goal_id}")
        return True
    
    def get_active_goals(self, max_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        アクティブな目標のリストを取得
        
        Args:
            max_count: 最大取得数（省略可）
            
        Returns:
            アクティブな目標のリスト（優先度順）
        """
        # 優先度でソート（高い順）
        sorted_goals = sorted(self.goals, key=lambda g: g["priority"], reverse=True)
        
        # 必要に応じて数を制限
        if max_count is not None:
            sorted_goals = sorted_goals[:max_count]
        
        return sorted_goals
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        次に取り組むべきタスク（サブタスク）を取得
        
        Returns:
            次のタスク（なければNone）
        """
        active_goals = self.get_active_goals()
        if not active_goals:
            return None
        
        for goal in active_goals:
            # 依存関係をチェック
            if any(self.get_goal(dep_id)["status"] != "completed" for dep_id in goal["dependencies"]):
                continue  # 依存する目標が完了していないためスキップ
            
            # サブタスクがない場合は分解
            if not goal["subtasks"]:
                self.decompose_goal(goal["id"])
            
            # 未完了のサブタスクを探す
            for subtask in goal["subtasks"]:
                if not subtask["completed"]:
                    return {
                        "goal_id": goal["id"],
                        "subtask_id": subtask["id"],
                        "description": subtask["description"],
                        "goal_description": goal["description"],
                        "priority": goal["priority"],
                        "goal_type": goal["type"]
                    }
        
        return None  # アクティブなタスクが見つからない
    
    def suggest_new_goals(self, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        新しい目標の提案
        
        Args:
            context: コンテキスト情報（省略可）
            
        Returns:
            目標提案のリスト
        """
        suggestions = []
        
        # アクティブな目標数が少ない場合は提案を増やす
        if len(self.goals) < self.config.get("min_active_goals", 3):
            # 知識獲得目標の提案
            suggestions.append({
                "type": "knowledge_acquisition",
                "description": "知識ベースの一般知識を拡充する",
                "priority": 3,
                "reason": "知識ベースの充実化"
            })
            
            # スキル開発目標の提案
            suggestions.append({
                "type": "skill_development",
                "description": "より効率的な情報検索手法を開発する",
                "priority": 4,
                "reason": "情報取得能力の向上"
            })
        
        # 最適化目標の定期的な提案
        last_optimization_goal = next(
            (g for g in self.goals + self.completed_goals 
             if g["type"] == "optimization" and 
             datetime.fromisoformat(g["created_at"]) > 
             datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)), 
            None
        )
        
        if not last_optimization_goal:
            suggestions.append({
                "type": "optimization",
                "description": "知識処理パイプラインの最適化",
                "priority": 3,
                "reason": "システム効率の向上"
            })
        
        # メンテナンス目標の提案
        if len(self.goals) > 10 or len(self.completed_goals) > 20:
            suggestions.append({
                "type": "maintenance",
                "description": "未使用の古い知識をレビューして整理する",
                "priority": 2,
                "reason": "知識ベースの整理"
            })
        
        return suggestions
    
    def review_goals(self) -> Dict[str, Any]:
        """
        目標の定期レビューを実施
        
        Returns:
            レビュー結果
        """
        now = time.time()
        if now < self.next_review_time:
            return {"status": "skipped", "message": "Review time not reached"}
        
        self.logger.info("Performing goal review")
        
        review_results = {
            "reviewed_goals": 0,
            "priority_adjustments": 0,
            "stalled_goals": 0,
            "goals_suggested": 0,
            "removed_goals": 0
        }
        
        # 各目標をレビュー
        for goal in self.goals[:]:  # コピーで反復して元のリストを変更
            # レビューカウントを増加
            goal["review_count"] += 1
            goal["last_reviewed"] = datetime.now().isoformat()
            
            # 停滞している目標を特定（進捗が乏しい）
            is_stalled = False
            if goal["review_count"] > 3 and goal["progress"] < 30:
                review_results["stalled_goals"] += 1
                is_stalled = True
                
                # 優先度を下げるか、古すぎる場合は削除
                if goal["review_count"] > 5:
                    self.goals.remove(goal)
                    review_results["removed_goals"] += 1
                    self.logger.info(f"Removed stalled goal: {goal['id']} - {goal['description']}")
                else:
                    # 優先度を1段階下げる（最低1）
                    if goal["priority"] > 1:
                        goal["priority"] -= 1
                        review_results["priority_adjustments"] += 1
                        self.logger.info(f"Lowered priority for stalled goal: {goal['id']}")
            
            # 依存関係の確認と更新
            for dep_id in goal["dependencies"][:]:  # コピーで反復
                dep_goal = self.get_goal(dep_id)
                if not dep_goal or dep_goal["status"] == "completed":
                    # 完了した依存を削除
                    goal["dependencies"].remove(dep_id)
            
            review_results["reviewed_goals"] += 1
        
        # 新しい目標の提案
        suggestions = self.suggest_new_goals()
        for suggestion in suggestions:
            # 1/3の確率で自動的に目標を追加
            if random.random() < 0.33:
                self.set_goal(
                    description=suggestion["description"],
                    goal_type=suggestion["type"],
                    priority=suggestion["priority"]
                )
                review_results["goals_suggested"] += 1
        
        # 次のレビュー時刻を設定
        self.next_review_time = now + self.config.get("review_interval_hours", 1) * 3600
        
        # データの保存
        self._save_data()
        
        self.logger.info(f"Goal review completed: {review_results}")
        return {"status": "success", "results": review_results}
    
    def _load_data(self) -> None:
        """データファイルから目標データをロード"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                
                self.goals = data.get("goals", [])
                self.completed_goals = data.get("completed_goals", [])
                
                self.logger.info(f"Loaded {len(self.goals)} active goals and {len(self.completed_goals)} completed goals")
            except Exception as e:
                self.logger.error(f"Error loading goal data: {str(e)}")
                # デフォルトの空のリストを使用
                self.goals = []
                self.completed_goals = []
    
    def _save_data(self) -> None:
        """目標データをデータファイルに保存"""
        try:
            # ディレクトリの確認
            os.makedirs(os.path.dirname(self.data_file) if os.path.dirname(self.data_file) else ".", exist_ok=True)
            
            data = {
                "goals": self.goals,
                "completed_goals": self.completed_goals,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.data_file, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug("Goal data saved")
        except Exception as e:
            self.logger.error(f"Error saving goal data: {str(e)}")
    
    def _has_circular_dependency(self, goal_id: str, dependency_id: str, visited: Optional[set] = None) -> bool:
        """目標間の循環依存をチェック"""
        if visited is None:
            visited = set()
        
        if goal_id in visited:
            return False
        
        visited.add(goal_id)
        
        # 依存先がチェック対象と一致する場合
        if goal_id == dependency_id:
            return True
        
        # このゴールの依存先をチェック
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        for dep_id in goal["dependencies"]:
            if self._has_circular_dependency(dep_id, dependency_id, visited):
                return True
        
        return False
    
    def get_goal_stats(self) -> Dict[str, Any]:
        """
        目標関連の統計情報を取得
        
        Returns:
            統計情報
        """
        # タイプ別の目標数
        type_counts = {}
        for goal in self.goals:
            goal_type = goal["type"]
            if goal_type not in type_counts:
                type_counts[goal_type] = 1
            else:
                type_counts[goal_type] += 1
        
        # 優先度別の目標数
        priority_counts = {}
        for goal in self.goals:
            priority = goal["priority"]
            if priority not in priority_counts:
                priority_counts[priority] = 1
            else:
                priority_counts[priority] += 1
        
        # 進捗率の平均
        avg_progress = sum(goal["progress"] for goal in self.goals) / len(self.goals) if self.goals else 0
        
        # 依存関係の数
        dependency_count = sum(len(goal["dependencies"]) for goal in self.goals)
        
        # 最近完了した目標
        recent_completed = []
        if self.completed_goals:
            sorted_completed = sorted(
                self.completed_goals,
                key=lambda g: g.get("completed_at", ""),
                reverse=True
            )
            recent_completed = sorted_completed[:5]  # 最新5件
        
        return {
            "active_goals": len(self.goals),
            "completed_goals": len(self.completed_goals),
            "goal_types": type_counts,
            "priority_distribution": priority_counts,
            "average_progress": avg_progress,
            "dependency_count": dependency_count,
            "recently_completed": [
                {"id": g["id"], "description": g["description"], "completed_at": g.get("completed_at")}
                for g in recent_completed
            ],
            "next_review_in_seconds": max(0, self.next_review_time - time.time())
        }
