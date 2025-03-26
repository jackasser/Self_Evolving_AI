import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import copy

class ProcessOptimizer:
    """
    思考プロセスとアルゴリズムの最適化を行うコンポーネント。
    処理効率を分析し、システムのパフォーマンスを向上させる。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        ProcessOptimizerの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.config = config.get("self_improvement", {})
        self.logger = logging.getLogger("process_optimizer")
        
        # 最適化履歴
        self.optimization_history = []
        
        # アクティブな最適化
        self.active_optimizations = {}
        
        # プロセス最適化設定
        self.optimization_settings = {
            "min_data_points": 5,
            "optimization_interval": 24,  # 時間
            "performance_threshold": 0.2,  # 20%の改善が必要
            "max_concurrent_optimizations": 3
        }
        
        # 処理タスクの履歴
        self.task_history = []
        
        # 許可された改善領域
        self.allowed_improvement_areas = self.config.get("improvement_areas", [
            "knowledge_base",
            "response_quality",
            "reasoning_process"
        ])
        
        self.logger.info("Process optimizer initialized")
    
    def record_task_execution(self, task_data: Dict[str, Any]) -> None:
        """
        タスク実行を記録
        
        Args:
            task_data: タスク実行データ
        """
        # 必要なフィールドを確認
        required_fields = ["task_id", "component", "start_time", "duration", "result_status"]
        
        for field in required_fields:
            if field not in task_data:
                self.logger.warning(f"Task execution record missing required field: {field}")
                return
        
        # 現在の時刻を追加
        task_data["recorded_at"] = datetime.now().isoformat()
        
        # 履歴に追加
        self.task_history.append(task_data)
        
        # 履歴が大きくなりすぎたら古いデータを削除
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
        
        self.logger.debug(f"Recorded task execution for {task_data['task_id']}")
    
    def analyze_process_efficiency(self, component: Optional[str] = None, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        処理効率を分析
        
        Args:
            component: 分析対象のコンポーネント（省略可）
            task_type: 分析対象のタスクタイプ（省略可）
            
        Returns:
            効率分析結果
        """
        if not self.task_history:
            return {"status": "insufficient_data"}
        
        # 対象タスクをフィルタリング
        filtered_tasks = self.task_history
        
        if component:
            filtered_tasks = [t for t in filtered_tasks if t.get("component") == component]
        
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t.get("task_type") == task_type]
        
        if len(filtered_tasks) < self.optimization_settings["min_data_points"]:
            return {
                "status": "insufficient_data",
                "message": f"少なくとも{self.optimization_settings['min_data_points']}件のデータポイントが必要です"
            }
        
        # 基本的な統計
        durations = [t.get("duration", 0) for t in filtered_tasks]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        # 結果ステータスの統計
        status_counts = {}
        for task in filtered_tasks:
            status = task.get("result_status", "unknown")
            if status not in status_counts:
                status_counts[status] = 1
            else:
                status_counts[status] += 1
        
        # コンポーネント別の統計
        component_stats = {}
        if not component:
            for task in filtered_tasks:
                comp = task.get("component", "unknown")
                if comp not in component_stats:
                    component_stats[comp] = {
                        "count": 1,
                        "total_duration": task.get("duration", 0)
                    }
                else:
                    component_stats[comp]["count"] += 1
                    component_stats[comp]["total_duration"] += task.get("duration", 0)
            
            # 平均を計算
            for comp in component_stats:
                if component_stats[comp]["count"] > 0:
                    component_stats[comp]["avg_duration"] = (
                        component_stats[comp]["total_duration"] / component_stats[comp]["count"]
                    )
        
        # ボトルネックの特定
        bottlenecks = []
        
        # 処理時間の長いタスク
        long_running_tasks = [t for t in filtered_tasks if t.get("duration", 0) > avg_duration * 1.5]
        if long_running_tasks:
            bottlenecks.append({
                "type": "long_running_tasks",
                "description": "平均処理時間の1.5倍を超えるタスク",
                "count": len(long_running_tasks),
                "examples": [t.get("task_id") for t in long_running_tasks[:3]]
            })
        
        # エラー率の高いタスク
        if "error" in status_counts:
            error_rate = status_counts.get("error", 0) / len(filtered_tasks)
            if error_rate > 0.1:  # 10%以上のエラー率
                bottlenecks.append({
                    "type": "high_error_rate",
                    "description": "エラー率が10%を超えるプロセス",
                    "error_rate": error_rate,
                    "error_count": status_counts.get("error", 0)
                })
        
        # コンポーネント間のバランスの悪さ
        if component_stats and len(component_stats) > 1:
            avg_times = [(comp, stats.get("avg_duration", 0)) for comp, stats in component_stats.items()]
            avg_times.sort(key=lambda x: x[1], reverse=True)
            
            if avg_times[0][1] > avg_times[-1][1] * 3:  # 最速と最遅のコンポーネントの差が3倍以上
                bottlenecks.append({
                    "type": "component_imbalance",
                    "description": "コンポーネント間の処理時間の不均衡",
                    "slowest": {
                        "component": avg_times[0][0],
                        "avg_duration": avg_times[0][1]
                    },
                    "fastest": {
                        "component": avg_times[-1][0],
                        "avg_duration": avg_times[-1][1]
                    }
                })
        
        # 冗長な操作の検出
        redundant_operations = self._detect_redundant_operations(filtered_tasks)
        
        # 分析結果
        efficiency_metrics = {
            "status": "success",
            "task_count": len(filtered_tasks),
            "time_metrics": {
                "average_processing_time": avg_duration,
                "max_processing_time": max_duration,
                "min_processing_time": min_duration,
                "processing_time_variance": sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            },
            "result_distribution": status_counts,
            "bottlenecks": bottlenecks,
            "redundant_operations": redundant_operations
        }
        
        if component_stats:
            efficiency_metrics["component_stats"] = component_stats
        
        self.logger.info(f"Completed process efficiency analysis with {len(filtered_tasks)} tasks")
        return efficiency_metrics
    
    def propose_optimizations(self, efficiency_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        効率メトリクスに基づいて最適化案を提案
        
        Args:
            efficiency_metrics: 効率分析の結果
            
        Returns:
            最適化提案のリスト
        """
        if efficiency_metrics.get("status") != "success":
            return []
        
        optimizations = []
        
        # ボトルネックへの対応
        for bottleneck in efficiency_metrics.get("bottlenecks", []):
            bottleneck_type = bottleneck.get("type", "")
            
            if bottleneck_type == "long_running_tasks":
                optimizations.append({
                    "id": f"opt_{int(time.time())}_{len(optimizations)}",
                    "type": "performance_optimization",
                    "target": "long_running_tasks",
                    "description": "長時間実行タスクの処理最適化",
                    "strategy": "タスク分割と並列処理の実装",
                    "expected_improvement": 0.3,  # 30%の改善を期待
                    "complexity": "medium",
                    "requires_review": self.config.get("requires_review", True)
                })
            
            elif bottleneck_type == "high_error_rate":
                optimizations.append({
                    "id": f"opt_{int(time.time())}_{len(optimizations)}",
                    "type": "reliability_optimization",
                    "target": "error_handling",
                    "description": "エラー処理メカニズムの強化",
                    "strategy": "例外処理とリトライロジックの改善",
                    "expected_improvement": 0.4,  # エラー率40%削減を期待
                    "complexity": "medium",
                    "requires_review": self.config.get("requires_review", True)
                })
            
            elif bottleneck_type == "component_imbalance":
                slow_component = bottleneck.get("slowest", {}).get("component", "unknown")
                optimizations.append({
                    "id": f"opt_{int(time.time())}_{len(optimizations)}",
                    "type": "performance_optimization",
                    "target": f"component_{slow_component}",
                    "description": f"{slow_component}コンポーネントの処理最適化",
                    "strategy": "アルゴリズム効率化とキャッシュ導入",
                    "expected_improvement": 0.35,  # 35%の改善を期待
                    "complexity": "high",
                    "requires_review": self.config.get("requires_review", True)
                })
        
        # 冗長操作の最適化
        if efficiency_metrics.get("redundant_operations"):
            optimizations.append({
                "id": f"opt_{int(time.time())}_{len(optimizations)}",
                "type": "efficiency_optimization",
                "target": "redundant_operations",
                "description": "冗長な処理の除去",
                "strategy": "処理の統合と重複排除",
                "expected_improvement": 0.2,  # 20%の改善を期待
                "complexity": "low",
                "requires_review": self.config.get("requires_review", True)
            })
        
        # 一般的なパフォーマンス最適化
        time_metrics = efficiency_metrics.get("time_metrics", {})
        if time_metrics.get("processing_time_variance", 0) > time_metrics.get("average_processing_time", 0):
            # 処理時間のバラツキが大きい場合
            optimizations.append({
                "id": f"opt_{int(time.time())}_{len(optimizations)}",
                "type": "stability_optimization",
                "target": "processing_stability",
                "description": "処理時間の安定化",
                "strategy": "処理フローの標準化と予測可能性の向上",
                "expected_improvement": 0.25,  # 25%の改善を期待
                "complexity": "medium",
                "requires_review": self.config.get("requires_review", True)
            })
        
        # 最適化の重複排除
        unique_optimizations = []
        optimization_targets = set()
        
        for opt in optimizations:
            target = opt.get("target", "")
            if target not in optimization_targets:
                unique_optimizations.append(opt)
                optimization_targets.add(target)
        
        self.logger.info(f"Proposed {len(unique_optimizations)} optimizations based on efficiency analysis")
        return unique_optimizations
    
    def implement_optimization(self, optimization_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        最適化を実装
        
        Args:
            optimization_id: 実装する最適化のID
            parameters: 最適化のパラメータ（省略可）
            
        Returns:
            実装結果
        """
        # 最適化案がすでにアクティブかチェック
        if optimization_id in self.active_optimizations:
            return {
                "status": "already_active",
                "message": f"最適化 {optimization_id} はすでにアクティブです"
            }
        
        # これは実際のシステムではより複雑な実装になる
        # このデモでは、最適化を記録し、擬似的な結果を返す
        
        implementation = {
            "id": optimization_id,
            "status": "implemented",
            "implemented_at": datetime.now().isoformat(),
            "parameters": parameters or {},
            "results": {
                "performance_impact": 0.15 + 0.1 * (hash(optimization_id) % 3),  # 擬似的な改善効果
                "stability_impact": 0.1,
                "resource_usage_impact": -0.05  # リソース使用量の減少
            }
        }
        
        # アクティブな最適化として記録
        self.active_optimizations[optimization_id] = implementation
        
        # 履歴に追加
        self.optimization_history.append({
            "event": "optimization_implemented",
            "optimization_id": optimization_id,
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters or {}
        })
        
        self.logger.info(f"Implemented optimization {optimization_id}")
        return implementation
    
    def evaluate_optimization(self, optimization_id: str) -> Dict[str, Any]:
        """
        実装された最適化の効果を評価
        
        Args:
            optimization_id: 評価する最適化のID
            
        Returns:
            評価結果
        """
        if optimization_id not in self.active_optimizations:
            return {
                "status": "not_found",
                "message": f"最適化 {optimization_id} は見つかりません"
            }
        
        optimization = self.active_optimizations[optimization_id]
        
        # 実装時刻を取得
        implemented_at = datetime.fromisoformat(optimization.get("implemented_at", datetime.now().isoformat()))
        
        # 実装前と後のタスクを比較
        before_tasks = [
            t for t in self.task_history 
            if datetime.fromisoformat(t.get("recorded_at", "")) < implemented_at
        ]
        
        after_tasks = [
            t for t in self.task_history 
            if datetime.fromisoformat(t.get("recorded_at", "")) >= implemented_at
        ]
        
        if len(before_tasks) < 5 or len(after_tasks) < 5:
            return {
                "status": "insufficient_data",
                "message": "効果を評価するためのデータが不足しています"
            }
        
        # 処理時間の比較
        before_avg_duration = sum(t.get("duration", 0) for t in before_tasks) / len(before_tasks)
        after_avg_duration = sum(t.get("duration", 0) for t in after_tasks) / len(after_tasks)
        
        # エラー率の比較
        before_errors = sum(1 for t in before_tasks if t.get("result_status") == "error")
        after_errors = sum(1 for t in after_tasks if t.get("result_status") == "error")
        
        before_error_rate = before_errors / len(before_tasks) if before_tasks else 0
        after_error_rate = after_errors / len(after_tasks) if after_tasks else 0
        
        # 改善率の計算
        if before_avg_duration > 0:
            duration_improvement = (before_avg_duration - after_avg_duration) / before_avg_duration
        else:
            duration_improvement = 0
        
        if before_error_rate > 0:
            error_rate_improvement = (before_error_rate - after_error_rate) / before_error_rate
        else:
            error_rate_improvement = 0 if after_error_rate == 0 else -1
        
        # 総合評価
        overall_impact = (duration_improvement * 0.7) + (error_rate_improvement * 0.3)
        
        evaluation = {
            "status": "success",
            "optimization_id": optimization_id,
            "metrics": {
                "before_implementation": {
                    "avg_duration": before_avg_duration,
                    "error_rate": before_error_rate,
                    "sample_size": len(before_tasks)
                },
                "after_implementation": {
                    "avg_duration": after_avg_duration,
                    "error_rate": after_error_rate,
                    "sample_size": len(after_tasks)
                },
                "improvements": {
                    "duration": duration_improvement,
                    "error_rate": error_rate_improvement,
                    "overall_impact": overall_impact
                }
            },
            "evaluation_status": (
                "success" if overall_impact >= 0.1 else 
                "neutral" if overall_impact >= -0.05 else 
                "regression"
            ),
            "evaluation_time": datetime.now().isoformat()
        }
        
        # 最適化の状態を更新
        self.active_optimizations[optimization_id]["evaluation"] = copy.deepcopy(evaluation["metrics"])
        self.active_optimizations[optimization_id]["evaluation_status"] = evaluation["evaluation_status"]
        
        # 履歴に追加
        self.optimization_history.append({
            "event": "optimization_evaluated",
            "optimization_id": optimization_id,
            "timestamp": datetime.now().isoformat(),
            "evaluation_status": evaluation["evaluation_status"],
            "overall_impact": overall_impact
        })
        
        self.logger.info(f"Evaluated optimization {optimization_id} with status: {evaluation['evaluation_status']}")
        return evaluation
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        最適化履歴を取得
        
        Returns:
            最適化イベントの履歴
        """
        return self.optimization_history
    
    def _detect_redundant_operations(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        冗長な操作を検出
        """
        redundant_ops = []
        
        # これは簡略化された実装
        # 実際のシステムではより高度なパターン検出を使用
        
        # 同一タスクが短時間に繰り返される場合
        task_sequence = {}
        
        for task in sorted(tasks, key=lambda t: t.get("start_time", "")):
            task_key = f"{task.get('component', '')}-{task.get('task_type', '')}"
            
            if task_key in task_sequence:
                prev_time = datetime.fromisoformat(task_sequence[task_key])
                curr_time = datetime.fromisoformat(task.get("start_time", datetime.now().isoformat()))
                
                time_diff = (curr_time - prev_time).total_seconds()
                
                if time_diff < 1.0:  # 1秒以内の同一タスク
                    redundant_ops.append({
                        "type": "repeated_task",
                        "description": f"短時間内に繰り返される同一タスク: {task_key}",
                        "time_difference": time_diff,
                        "task_ids": [task.get("task_id", "unknown")]
                    })
            
            task_sequence[task_key] = task.get("start_time", "")
        
        # 失敗後の無意味なリトライ
        for i in range(len(tasks) - 1):
            if (tasks[i].get("result_status") == "error" and
                tasks[i+1].get("task_id") == tasks[i].get("task_id") and
                tasks[i+1].get("result_status") == "error"):
                
                redundant_ops.append({
                    "type": "failed_retry",
                    "description": f"失敗後の同一条件での無意味なリトライ: {tasks[i].get('task_id', 'unknown')}",
                    "task_ids": [tasks[i].get("task_id", "unknown"), tasks[i+1].get("task_id", "unknown")]
                })
        
        return redundant_ops
