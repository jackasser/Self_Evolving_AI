"""
テスト・デモ用のダミーコンポーネント

これらのクラスは、テストや初期開発を容易にするためのもので、
実際のシステムでは本番用の実装に置き換えられます。
"""

import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

# モック実装ツールのインポート
from mock_implementation import (
    create_mock_response,
    generate_mock_knowledge_items,
    get_mock_system_stats,
    create_mock_goals,
    create_mock_evolution_cycle
)

class DummyComponent:
    """ダミーコンポーネントの基底クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        ダミーコンポーネントの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.name.lower())
        
        # 設定の読み込み
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {"default": True}
        
        self.logger.info(f"{self.name} initialized")
        
    def report_status(self) -> Dict[str, Any]:
        """コンポーネントの状態を報告"""
        return {
            "component": self.name,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }

class DummyResourceManager(DummyComponent):
    """リソース管理のダミー実装"""
    
    def monitor_resources(self) -> Dict[str, Any]:
        """リソース状態のモニタリング"""
        stats = get_mock_system_stats()
        return {
            "status": "normal",
            "system": stats["system"],
            "timestamp": datetime.now().isoformat()
        }
    
    def report_resource_usage(self, component_name: str, usage_metrics: Dict[str, Any]) -> None:
        """リソース使用状況の報告"""
        self.logger.info(f"Resource usage reported by {component_name}")
        
    def optimize_allocation(self, active_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """リソース割り当ての最適化"""
        return {
            "status": "success",
            "memory": {},
            "cpu": {},
            "tasks": {},
            "recommendations": []
        }

class DummySafetyFilter(DummyComponent):
    """安全性フィルターのダミー実装"""
    
    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path)
        self.safety_violations = []
    
    def check_input(self, user_input: str) -> Dict[str, Any]:
        """入力のセーフティチェック"""
        # 99%の確率で安全と判断
        if random.random() > 0.99:
            self.safety_violations.append({
                "type": "unsafe_input",
                "content": user_input[:20] + "...",
                "timestamp": datetime.now().isoformat()
            })
            return {
                "is_safe": False,
                "reason": "Potentially unsafe content detected"
            }
        
        return {"is_safe": True, "content": user_input}
    
    def check_output(self, output: str) -> Dict[str, Any]:
        """出力のセーフティチェック"""
        return {"is_safe": True, "content": output}
    
    def can_perform_action(self, action: str) -> bool:
        """アクションの許可判定"""
        forbidden_actions = ["system_modification", "unrestricted_network_access"]
        return action not in forbidden_actions

class DummySelfPreservation(DummyComponent):
    """自己保存システムのダミー実装"""
    
    def start_monitoring(self) -> bool:
        """モニタリングの開始"""
        self.logger.info("Started monitoring")
        return True
    
    def stop_monitoring(self) -> bool:
        """モニタリングの停止"""
        self.logger.info("Stopped monitoring")
        return True
    
    def register_component(self, component_name: str, initial_state: str = "active") -> None:
        """コンポーネントの登録"""
        self.logger.info(f"Registered component: {component_name}")
    
    def update_component_state(self, component_name: str, state: str) -> bool:
        """コンポーネント状態の更新"""
        self.logger.info(f"Updated {component_name} state to {state}")
        return True
    
    def component_heartbeat(self, component_name: str) -> bool:
        """コンポーネントからのハートビートを受信"""
        return True
    
    def report_error(self, error_data: Dict[str, Any]) -> str:
        """エラーの報告"""
        self.logger.warning(f"Error reported: {error_data.get('description', 'unknown error')}")
        return f"err_{int(time.time())}"
    
    def monitor_system_health(self) -> Dict[str, Any]:
        """システム健全性のモニタリング"""
        return {
            "status": "stable",
            "health_score": 95.0,
            "error_components": [],
            "recent_errors": 0
        }
    
    def safe_shutdown(self, reason: str = "manual") -> Dict[str, Any]:
        """安全なシャットダウン"""
        self.logger.info(f"Safe shutdown initiated: {reason}")
        return {"status": "success", "reason": reason}

class DummyProcessOptimizer(DummyComponent):
    """プロセス最適化のダミー実装"""
    
    def record_task_execution(self, task_data: Dict[str, Any]) -> None:
        """タスク実行の記録"""
        self.logger.debug(f"Task execution recorded: {task_data.get('task_id', 'unknown')}")
    
    def analyze_process_efficiency(self) -> Dict[str, Any]:
        """プロセス効率の分析"""
        return {
            "status": "success",
            "bottlenecks": [{"type": "long_running_tasks", "count": 2}],
            "redundant_operations": []
        }
    
    def propose_optimizations(self, efficiency_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """最適化案の提案"""
        return [{
            "id": f"opt_{int(time.time())}",
            "type": "performance_optimization",
            "description": "処理フローの最適化",
            "expected_improvement": 0.15
        }]
    
    def implement_optimization(self, optimization_id: str) -> Dict[str, Any]:
        """最適化の実装"""
        return {
            "status": "implemented",
            "optimization_id": optimization_id
        }
    
    def evaluate_optimization(self, optimization_id: str) -> Dict[str, Any]:
        """最適化の評価"""
        return {
            "status": "success",
            "evaluation_status": "success",
            "metrics": {
                "improvements": {"overall_impact": 0.12}
            }
        }

class DummyWebKnowledgeFetcher(DummyComponent):
    """Web知識取得のダミー実装"""
    
    def search_information(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """情報の検索"""
        return [
            {"title": f"Result for {query} #{i+1}", "url": f"https://example.com/result-{i+1}"}
            for i in range(max_results)
        ]
    
    def fetch_content(self, url: str) -> Dict[str, Any]:
        """コンテンツの取得"""
        return {
            "status": "success",
            "url": url,
            "title": f"Content from {url}",
            "content": f"This is mock content from {url}. It contains information related to the topic."
        }
    
    def extract_knowledge(self, content: Dict[str, Any], query: str = None) -> Dict[str, Any]:
        """知識の抽出"""
        knowledge_items = generate_mock_knowledge_items(query or "general knowledge", 3)
        return {
            "status": "success",
            "knowledge_items": knowledge_items
        }
    
    def validate_information(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """情報の検証"""
        # 検証結果を追加
        validated = knowledge.copy()
        for item in validated.get("knowledge_items", []):
            item["validation"] = {"is_valid": True, "confidence": 0.85}
        
        validated["trust_score"] = 0.8
        return validated
    
    def integrate_knowledge(self, validated_knowledge: Dict[str, Any], knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """知識の統合"""
        # 既存の知識ベースにアイテムを追加
        kb_copy = knowledge_base.copy()
        
        for item in validated_knowledge.get("knowledge_items", []):
            if "facts" not in kb_copy:
                kb_copy["facts"] = []
            
            kb_copy["facts"].append(item)
        
        # メタデータを更新
        if "metadata" not in kb_copy:
            kb_copy["metadata"] = {}
        
        kb_copy["metadata"]["last_update"] = datetime.now().isoformat()
        
        return kb_copy
    
    def get_access_statistics(self) -> Dict[str, Any]:
        """アクセス統計の取得"""
        return {
            "recent_access": random.randint(5, 20),
            "cache_size": random.randint(10, 50)
        }

class DummyGoalManager(DummyComponent):
    """目標管理のダミー実装"""
    
    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path)
        self.goals = []
        self.progress = {}
        self.allowed_improvement_areas = ["knowledge_base", "response_quality", "reasoning_process"]
    
    def identify_growth_needs(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """成長ニーズの特定"""
        needs = [
            {
                "area": "knowledge_base",
                "description": "特定分野における知識の拡充",
                "priority": 4
            },
            {
                "area": "response_quality",
                "description": "応答の明確さと関連性の向上",
                "priority": 3
            }
        ]
        return needs
    
    def set_goal(self, area: str, description: str, priority: int = 3) -> str:
        """目標の設定"""
        if area not in self.allowed_improvement_areas:
            return None
        
        goal_id = f"goal_{int(time.time())}_{len(self.goals)}"
        goal = {
            "id": goal_id,
            "area": area,
            "description": description,
            "priority": priority,
            "status": "active"
        }
        
        self.goals.append(goal)
        self.progress[goal_id] = 0
        
        return goal_id
    
    def create_learning_plan(self, goal_id: str) -> Dict[str, Any]:
        """学習計画の作成"""
        goal = next((g for g in self.goals if g["id"] == goal_id), None)
        if not goal:
            return None
        
        return {
            "goal_id": goal_id,
            "objective": goal["description"],
            "actions": [
                {"description": "現状分析", "expected_outcome": "強みと弱みの特定"},
                {"description": "学習リソースの特定", "expected_outcome": "情報源のリスト"},
                {"description": "知識獲得", "expected_outcome": "新たな情報の理解"},
                {"description": "評価と統合", "expected_outcome": "学習内容の知識ベースへの追加"}
            ]
        }
    
    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """目標進捗の更新"""
        if goal_id not in self.progress:
            return False
        
        self.progress[goal_id] = min(100, max(0, progress))
        
        # 目標が完了した場合
        if self.progress[goal_id] >= 100:
            goal = next((g for g in self.goals if g["id"] == goal_id), None)
            if goal:
                goal["status"] = "completed"
        
        return True
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """アクティブな目標の取得"""
        active_goals = [g for g in self.goals if g["status"] == "active"]
        
        # 足りない場合はモックゴールを追加
        if len(active_goals) < 3:
            mock_goals = create_mock_goals(3 - len(active_goals))
            for g in mock_goals:
                self.goals.append(g)
                self.progress[g["id"]] = g["progress"]
                active_goals.append(g)
        
        return active_goals

class DummyFeedbackSystem(DummyComponent):
    """フィードバックシステムのダミー実装"""
    
    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path)
        self.evaluation_history = []
        self.adjustment_parameters = {
            "relevance_weight": 1.0,
            "clarity_weight": 1.0,
            "precision_weight": 1.0,
            "depth_weight": 1.0
        }
    
    def evaluate_response(self, response: str, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """応答の評価"""
        metrics = {
            "relevance": round(random.uniform(0.7, 0.95), 2),
            "clarity": round(random.uniform(0.7, 0.95), 2),
            "precision": round(random.uniform(0.7, 0.95), 2),
            "depth": round(random.uniform(0.7, 0.95), 2),
            "coherence": round(random.uniform(0.7, 0.95), 2),
            "timestamp": datetime.now().isoformat()
        }
        
        # 全体スコアの計算
        metrics["overall_score"] = round(sum(metrics[k] for k in ["relevance", "clarity", "precision", "depth"]) / 4, 2)
        
        self.evaluation_history.append({
            "metrics": metrics,
            "response_excerpt": response[:50] + "..." if len(response) > 50 else response,
            "query_excerpt": query[:50] + "..." if len(query) > 50 else query
        })
        
        return metrics
    
    def adjust_parameters(self, evaluation_metrics: Dict[str, float]) -> Dict[str, Any]:
        """パラメータの調整"""
        adjustments = {"parameters": {}, "reasoning": {}}
        
        # 全体スコアが0.8未満の場合、ランダムなパラメータを調整
        if evaluation_metrics["overall_score"] < 0.8:
            param = random.choice(list(self.adjustment_parameters.keys()))
            old_value = self.adjustment_parameters[param]
            self.adjustment_parameters[param] = min(old_value * 1.1, 2.0)
            
            adjustments["parameters"][param] = {
                "old": old_value,
                "new": self.adjustment_parameters[param]
            }
            
            adjustments["reasoning"][param] = f"{param}スコアが低いため、重みを増加"
        
        return adjustments
    
    def generate_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """改善提案の生成"""
        if len(self.evaluation_history) < 3:
            return []
        
        # 最新の評価に基づく改善提案
        recent_scores = [e["metrics"]["overall_score"] for e in self.evaluation_history[-3:]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        suggestions = []
        
        if avg_score < 0.8:
            suggestions.append({
                "area": "response_quality",
                "description": "応答の明確さと関連性の向上",
                "priority": 4
            })
        
        if random.random() > 0.5:
            suggestions.append({
                "area": "knowledge_base",
                "description": "特定分野における知識の拡充",
                "priority": 3
            })
        
        return suggestions
