import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class GoalManager:
    """
    自己成長のための目標設定と管理を行うコンポーネント。
    自律的な学習と最適化のための目標を設定・追跡する。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        GoalManagerの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.config = config.get("self_improvement", {})
        
        # ロギングの設定
        self.logger = logging.getLogger("goal_manager")
        
        # 目標管理用の構造
        self.goals = []
        self.priorities = {}
        self.progress = {}
        
        # 許可された改善領域
        self.allowed_improvement_areas = self.config.get("improvement_areas", [
            "knowledge_base",
            "response_quality",
            "reasoning_process"
        ])
        
        # 目標の履歴
        self.goal_history = []
        
        self.logger.info("Goal Manager initialized")
    
    def identify_growth_needs(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        コンテキストから成長のニーズを特定し、目標候補を生成する
        
        Args:
            context: システムコンテキスト（ユーザー対話履歴、学習状態など）
            
        Returns:
            成長ニーズのリスト
        """
        growth_needs = []
        
        # セッション履歴からのパターン分析
        if "session_history" in context:
            needs = self._analyze_session_history(context["session_history"])
            growth_needs.extend(needs)
        
        # 学習済み情報からの知識ギャップ分析
        if "learned_preferences" in context:
            needs = self._analyze_knowledge_gaps(context["learned_preferences"])
            growth_needs.extend(needs)
        
        # プランニング履歴からの推論能力分析
        if "active_plans" in context:
            needs = self._analyze_reasoning_capability(context["active_plans"])
            growth_needs.extend(needs)
        
        # 改善領域フィルタリング
        growth_needs = [need for need in growth_needs 
                        if need["area"] in self.allowed_improvement_areas]
        
        self.logger.info(f"Identified {len(growth_needs)} growth needs")
        return growth_needs
    
    def set_goal(self, area: str, description: str, priority: int = 1) -> str:
        """
        新しい成長目標を設定
        
        Args:
            area: 改善領域
            description: 目標の説明
            priority: 優先度（1-5、5が最高）
            
        Returns:
            生成された目標ID
        """
        if area not in self.allowed_improvement_areas:
            self.logger.warning(f"Attempted to set goal in unauthorized area: {area}")
            return None
        
        # 目標IDの生成
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.goals)}"
        
        # 目標の作成
        goal = {
            "id": goal_id,
            "area": area,
            "description": description,
            "priority": max(1, min(5, priority)),  # 1-5の範囲に制限
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "requires_review": self.config.get("requires_review", True)
        }
        
        # 目標の追加
        self.goals.append(goal)
        self.priorities[goal_id] = goal["priority"]
        self.progress[goal_id] = 0
        
        # 履歴に追加
        self.goal_history.append({
            "event": "goal_created",
            "goal_id": goal_id,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"Set new goal: {goal_id} - {description}")
        return goal_id
    
    def create_learning_plan(self, goal_id: str) -> Dict[str, Any]:
        """
        特定の目標に対する学習計画を作成
        
        Args:
            goal_id: 対象となる目標のID
            
        Returns:
            学習計画
        """
        goal = next((g for g in self.goals if g["id"] == goal_id), None)
        if not goal:
            self.logger.warning(f"Attempted to create plan for non-existent goal: {goal_id}")
            return None
        
        # 目標の種類に基づいた計画の作成
        area = goal["area"]
        
        # 基本計画構造
        plan = {
            "goal_id": goal_id,
            "objective": goal["description"],
            "metrics": {},
            "actions": [],
            "timeline": {},
            "resources": [],
            "created_at": datetime.now().isoformat(),
            "status": "pending" if goal["requires_review"] else "active"
        }
        
        # 領域固有の計画詳細を追加
        if area == "knowledge_base":
            plan = self._create_knowledge_plan(plan, goal)
        elif area == "response_quality":
            plan = self._create_quality_plan(plan, goal)
        elif area == "reasoning_process":
            plan = self._create_reasoning_plan(plan, goal)
        
        self.logger.info(f"Created learning plan for goal {goal_id}")
        return plan
    
    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """
        目標の進捗を更新
        
        Args:
            goal_id: 対象となる目標のID
            progress: 進捗度（0-100）
            
        Returns:
            更新が成功したかどうか
        """
        if goal_id not in self.progress:
            self.logger.warning(f"Attempted to update non-existent goal: {goal_id}")
            return False
        
        # 前回の進捗を記録
        previous_progress = self.progress[goal_id]
        
        # 進捗を更新（0-100の範囲に制限）
        self.progress[goal_id] = max(0, min(100, progress))
        
        # 履歴に追加
        self.goal_history.append({
            "event": "progress_updated",
            "goal_id": goal_id,
            "previous": previous_progress,
            "current": self.progress[goal_id],
            "timestamp": datetime.now().isoformat()
        })
        
        # 目標が完了した場合のチェック
        if self.progress[goal_id] >= 100:
            goal = next((g for g in self.goals if g["id"] == goal_id), None)
            if goal:
                goal["status"] = "completed"
                self.goal_history.append({
                    "event": "goal_completed",
                    "goal_id": goal_id,
                    "timestamp": datetime.now().isoformat()
                })
                self.logger.info(f"Goal {goal_id} completed")
        
        self.logger.info(f"Updated goal {goal_id} progress: {self.progress[goal_id]}%")
        return True
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        アクティブな目標のリストを取得
        
        Returns:
            アクティブな目標のリスト
        """
        active_goals = [g for g in self.goals if g["status"] == "active"]
        
        # 優先度でソート
        active_goals.sort(key=lambda g: g["priority"], reverse=True)
        
        return active_goals
    
    def _analyze_session_history(self, session_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        セッション履歴を分析して成長ニーズを抽出
        """
        needs = []
        
        # これは簡略化された実装
        # 実際のシステムではより高度なNLPやパターン認識を使用
        
        # ユーザーの質問の種類をカウント
        question_types = {}
        
        for entry in session_history:
            if entry.get("role") == "user":
                content = entry.get("content", "").lower()
                
                # 質問タイプの検出
                if "how" in content or "why" in content:
                    question_type = "explanatory"
                elif "what is" in content or "who is" in content or "where is" in content:
                    question_type = "informational"
                elif "can you" in content or "please" in content:
                    question_type = "request"
                else:
                    question_type = "other"
                
                # カウント
                if question_type not in question_types:
                    question_types[question_type] = 1
                else:
                    question_types[question_type] += 1
        
        # 頻出パターンに基づくニーズの特定
        for q_type, count in question_types.items():
            if count >= 3:  # 閾値
                if q_type == "explanatory":
                    needs.append({
                        "area": "reasoning_process",
                        "description": "説明能力の向上",
                        "priority": min(count // 3, 5)  # カウントに基づく優先度
                    })
                elif q_type == "informational":
                    needs.append({
                        "area": "knowledge_base",
                        "description": "知識ベースの拡張",
                        "priority": min(count // 3, 5)
                    })
        
        return needs
    
    def _analyze_knowledge_gaps(self, learned_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        学習済み情報を分析して知識ギャップを特定
        """
        needs = []
        
        # これは簡略化された実装
        # 実際のシステムではより高度な知識表現と分析を使用
        
        # 特定の好みに基づく知識ニーズの特定
        if "response_length" in learned_preferences:
            if learned_preferences["response_length"] == "detailed":
                needs.append({
                    "area": "knowledge_base",
                    "description": "より詳細な情報提供のための知識拡張",
                    "priority": 4
                })
        
        if "include_examples" in learned_preferences and learned_preferences["include_examples"]:
            needs.append({
                "area": "knowledge_base",
                "description": "具体例のレパートリー拡大",
                "priority": 3
            })
        
        return needs
    
    def _analyze_reasoning_capability(self, active_plans: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        計画能力を分析して推論能力のニーズを特定
        """
        needs = []
        
        # これは簡略化された実装
        # 実際のシステムではより高度な計画評価を使用
        
        if not active_plans:
            return needs
        
        # 計画の複雑さを評価
        avg_steps = sum(len(plan.get("tasks", [])) for plan in active_plans.values()) / len(active_plans)
        
        if avg_steps < 3:
            needs.append({
                "area": "reasoning_process",
                "description": "より複雑な計画立案能力の向上",
                "priority": 3
            })
        
        return needs
    
    def _create_knowledge_plan(self, plan: Dict[str, Any], goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        知識ベース改善のための計画を作成
        """
        plan["metrics"] = {
            "coverage_increase": "目標領域での知識カバレッジ増加率",
            "accuracy_improvement": "既存知識の正確性向上率"
        }
        
        plan["actions"] = [
            {
                "description": "現在の知識ベースの分析",
                "expected_outcome": "強みと弱みの特定",
                "completion_criteria": "領域別の知識マップ作成完了"
            },
            {
                "description": "優先知識領域の特定",
                "expected_outcome": "優先的に拡張すべき領域のリスト",
                "completion_criteria": "優先リストの作成完了"
            },
            {
                "description": "知識獲得プロセスの実施",
                "expected_outcome": "新たな情報の構造化された表現",
                "completion_criteria": "知識ベースへの統合完了"
            },
            {
                "description": "獲得知識の検証",
                "expected_outcome": "新知識の正確性と一貫性の確認",
                "completion_criteria": "検証テスト完了"
            }
        ]
        
        return plan
    
    def _create_quality_plan(self, plan: Dict[str, Any], goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        応答品質改善のための計画を作成
        """
        plan["metrics"] = {
            "relevance_score": "応答の関連性スコア",
            "clarity_score": "応答の明確さスコア",
            "user_satisfaction": "ユーザー満足度の推定値"
        }
        
        plan["actions"] = [
            {
                "description": "現在の応答品質の評価",
                "expected_outcome": "品質メトリクスのベースライン確立",
                "completion_criteria": "評価レポート作成完了"
            },
            {
                "description": "品質向上のためのパラメータ最適化",
                "expected_outcome": "調整されたパラメータセット",
                "completion_criteria": "パラメータ調整完了"
            },
            {
                "description": "応答フォーマットの改善",
                "expected_outcome": "より明確で構造化された応答テンプレート",
                "completion_criteria": "新テンプレート作成完了"
            },
            {
                "description": "品質向上の効果測定",
                "expected_outcome": "改善前後の比較データ",
                "completion_criteria": "効果測定完了"
            }
        ]
        
        return plan
    
    def _create_reasoning_plan(self, plan: Dict[str, Any], goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        推論プロセス改善のための計画を作成
        """
        plan["metrics"] = {
            "logical_coherence": "推論の論理的一貫性スコア",
            "step_efficiency": "推論ステップの効率性",
            "conclusion_validity": "結論の妥当性スコア"
        }
        
        plan["actions"] = [
            {
                "description": "現在の推論プロセスの分析",
                "expected_outcome": "推論フローの強みと弱みの特定",
                "completion_criteria": "分析レポート作成完了"
            },
            {
                "description": "推論アルゴリズムの最適化",
                "expected_outcome": "改善された推論ステップの順序と構造",
                "completion_criteria": "アルゴリズム最適化完了"
            },
            {
                "description": "エッジケース処理の強化",
                "expected_outcome": "例外的シナリオでの推論能力向上",
                "completion_criteria": "エッジケースライブラリ作成完了"
            },
            {
                "description": "推論プロセスの効果測定",
                "expected_outcome": "最適化前後の性能比較データ",
                "completion_criteria": "効果測定完了"
            }
        ]
        
        return plan
