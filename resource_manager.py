import logging
import json
import time
import os
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime

class ResourceManager:
    """
    計算リソースの効率的管理と割り当てを行うコンポーネント。
    システムのパフォーマンスを監視し、リソース使用を最適化する。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        ResourceManagerの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.config = config
        self.logger = logging.getLogger("resource_manager")
        
        # リソース割り当て設定
        self.resource_allocation = {
            "memory": {},
            "cpu": {},
            "storage": {}
        }
        
        # パフォーマンスメトリクスの履歴
        self.performance_history = []
        
        # リソース使用量の閾値
        self.thresholds = {
            "memory_warning": 80,  # パーセント
            "memory_critical": 90,
            "cpu_warning": 70,
            "cpu_critical": 85,
            "storage_warning": 85,
            "storage_critical": 95
        }
        
        # コンポーネント優先度（リソース競合時）
        self.component_priorities = {
            "safety_filter": 10,  # 最高優先度
            "planner": 8,
            "learning_manager": 6,
            "self_feedback": 5,
            "goal_manager": 4
        }
        
        self.logger.info("Resource manager initialized")
    
    def monitor_resources(self) -> Dict[str, Any]:
        """
        システムリソースの現在の使用状況をモニタリング
        
        Returns:
            リソース使用状況のメトリクス
        """
        # メモリ使用量
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        # CPU使用量
        cpu_usage_percent = psutil.cpu_percent(interval=0.1)
        
        # ディスク使用量
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # プロセス情報
        process = psutil.Process(os.getpid())
        process_memory_mb = process.memory_info().rss / 1024 / 1024
        process_cpu_percent = process.cpu_percent(interval=0.1)
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "memory_total_mb": memory.total / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "memory_usage_percent": memory_usage_percent,
                "cpu_usage_percent": cpu_usage_percent,
                "disk_total_gb": disk.total / 1024 / 1024 / 1024,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "disk_usage_percent": disk_usage_percent
            },
            "process": {
                "memory_mb": process_memory_mb,
                "cpu_percent": process_cpu_percent
            },
            "status": self._determine_resource_status(memory_usage_percent, cpu_usage_percent, disk_usage_percent)
        }
        
        # 履歴に追加
        self.performance_history.append(metrics)
        
        # 履歴が大きくなりすぎたら古いエントリを削除
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # 警告レベルの確認とログ記録
        self._log_resource_warnings(metrics)
        
        return metrics
    
    def optimize_allocation(self, active_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        アクティブタスクに基づいてリソースを最適化
        
        Args:
            active_tasks: 現在実行中または計画されているタスクのリスト
            
        Returns:
            リソース割り当て計画
        """
        # 現在のリソース状況を取得
        current_metrics = self.monitor_resources()
        
        # ステータスに基づいた最適化戦略
        status = current_metrics["status"]
        
        # リソース割り当て計画
        allocation_plan = {
            "memory": {},
            "cpu": {},
            "tasks": {},
            "recommendations": []
        }
        
        # タスクの優先度付け
        prioritized_tasks = self._prioritize_tasks(active_tasks)
        
        # ステータスに応じた割り当て戦略
        if status == "critical":
            allocation_plan = self._critical_allocation(prioritized_tasks, current_metrics)
        elif status == "warning":
            allocation_plan = self._warning_allocation(prioritized_tasks, current_metrics)
        else:  # normal
            allocation_plan = self._normal_allocation(prioritized_tasks, current_metrics)
        
        # 割り当てを更新
        self.resource_allocation = allocation_plan
        
        self.logger.info(f"Resource allocation optimized with status: {status}")
        return allocation_plan
    
    def get_component_resources(self, component_name: str) -> Dict[str, Any]:
        """
        特定のコンポーネントに割り当てられたリソースを取得
        
        Args:
            component_name: リソースを取得するコンポーネントの名前
            
        Returns:
            割り当てられたリソース情報
        """
        resources = {
            "memory": self.resource_allocation["memory"].get(component_name, 0),
            "cpu": self.resource_allocation["cpu"].get(component_name, 0),
            "priority": self.component_priorities.get(component_name, 1)
        }
        
        return resources
    
    def report_resource_usage(self, component_name: str, usage_metrics: Dict[str, Any]) -> None:
        """
        コンポーネントからのリソース使用報告を処理
        
        Args:
            component_name: 報告するコンポーネントの名前
            usage_metrics: 使用量メトリクス
        """
        # これは実際のシステムでは使用されるが、このデモでは単純にログに記録
        self.logger.info(f"Resource usage reported by {component_name}: {json.dumps(usage_metrics)}")
        
        # 必要に応じて割り当てを微調整
        # この実装はシンプルなデモ
        if "memory_mb" in usage_metrics and "cpu_percent" in usage_metrics:
            if usage_metrics["memory_mb"] > self.resource_allocation["memory"].get(component_name, 0) * 1.2:
                # 使用量が割り当ての120%を超えた場合、割り当てを増やす
                self.resource_allocation["memory"][component_name] = usage_metrics["memory_mb"] * 1.1
                self.logger.info(f"Increased memory allocation for {component_name}")
    
    def get_resource_trend(self, metric_name: str, duration_minutes: int = 10) -> Dict[str, Any]:
        """
        特定のメトリクスの時間的傾向を取得
        
        Args:
            metric_name: 分析するメトリクスの名前（例：memory_usage_percent）
            duration_minutes: 分析する期間（分）
            
        Returns:
            傾向分析データ
        """
        if not self.performance_history:
            return {"status": "insufficient_data"}
        
        # 現在の時刻
        now = datetime.now()
        
        # 指定期間内のデータをフィルタリング
        filtered_data = []
        
        for entry in self.performance_history:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            time_diff = (now - entry_time).total_seconds() / 60
            
            if time_diff <= duration_minutes:
                # システムメトリクス内のキーをチェック
                if metric_name in entry["system"]:
                    filtered_data.append({
                        "timestamp": entry["timestamp"],
                        "value": entry["system"][metric_name]
                    })
                # プロセスメトリクス内のキーをチェック
                elif metric_name in entry["process"]:
                    filtered_data.append({
                        "timestamp": entry["timestamp"],
                        "value": entry["process"][metric_name]
                    })
        
        if not filtered_data:
            return {"status": "metric_not_found"}
        
        # データポイント数が少なすぎる場合
        if len(filtered_data) < 3:
            return {"status": "insufficient_data_points"}
        
        # 基本的な統計
        values = [point["value"] for point in filtered_data]
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # トレンド分析
        first_value = values[0]
        last_value = values[-1]
        trend_direction = "steady"
        
        if last_value > first_value * 1.1:
            trend_direction = "increasing"
        elif last_value < first_value * 0.9:
            trend_direction = "decreasing"
        
        # 変化率
        if first_value > 0:
            change_rate = (last_value - first_value) / first_value * 100
        else:
            change_rate = 0
        
        trend_data = {
            "status": "success",
            "metric": metric_name,
            "duration_minutes": duration_minutes,
            "data_points": len(filtered_data),
            "statistics": {
                "average": avg_value,
                "minimum": min_value,
                "maximum": max_value,
                "first": first_value,
                "last": last_value
            },
            "trend": {
                "direction": trend_direction,
                "change_percent": change_rate
            }
        }
        
        return trend_data
    
    def _determine_resource_status(self, memory_percent: float, cpu_percent: float, disk_percent: float) -> str:
        """
        リソース使用量に基づいたシステム状態を判断
        """
        if (memory_percent >= self.thresholds["memory_critical"] or
            cpu_percent >= self.thresholds["cpu_critical"] or
            disk_percent >= self.thresholds["storage_critical"]):
            return "critical"
        
        if (memory_percent >= self.thresholds["memory_warning"] or
            cpu_percent >= self.thresholds["cpu_warning"] or
            disk_percent >= self.thresholds["storage_warning"]):
            return "warning"
        
        return "normal"
    
    def _log_resource_warnings(self, metrics: Dict[str, Any]) -> None:
        """
        リソース警告をログに記録
        """
        system = metrics["system"]
        status = metrics["status"]
        
        if status == "critical":
            # 重大なリソース警告
            if system["memory_usage_percent"] >= self.thresholds["memory_critical"]:
                self.logger.warning(f"CRITICAL: Memory usage at {system['memory_usage_percent']}%")
            
            if system["cpu_usage_percent"] >= self.thresholds["cpu_critical"]:
                self.logger.warning(f"CRITICAL: CPU usage at {system['cpu_usage_percent']}%")
            
            if system["disk_usage_percent"] >= self.thresholds["storage_critical"]:
                self.logger.warning(f"CRITICAL: Disk usage at {system['disk_usage_percent']}%")
        
        elif status == "warning":
            # 警告レベルのリソース状態
            if system["memory_usage_percent"] >= self.thresholds["memory_warning"]:
                self.logger.info(f"WARNING: Memory usage at {system['memory_usage_percent']}%")
            
            if system["cpu_usage_percent"] >= self.thresholds["cpu_warning"]:
                self.logger.info(f"WARNING: CPU usage at {system['cpu_usage_percent']}%")
            
            if system["disk_usage_percent"] >= self.thresholds["storage_warning"]:
                self.logger.info(f"WARNING: Disk usage at {system['disk_usage_percent']}%")
    
    def _prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        タスクの優先順位付け
        """
        # まず安全性関連タスクを優先
        for task in tasks:
            component = task.get("component", "")
            priority = self.component_priorities.get(component, 1)
            
            # 安全性に関連するタスクはさらに優先度を高くする
            if "safety" in task.get("tags", []):
                priority += 5
            
            # ユーザー対応タスクも優先
            if "user_facing" in task.get("tags", []):
                priority += 3
            
            task["calculated_priority"] = priority
        
        # 優先度でソート
        prioritized = sorted(tasks, key=lambda t: t.get("calculated_priority", 0), reverse=True)
        return prioritized
    
    def _critical_allocation(self, prioritized_tasks: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        リソースが危機的状況での割り当て戦略
        """
        # 緊急節約モード - 最小限のリソースを割り当て
        allocation = {
            "memory": {},
            "cpu": {},
            "tasks": {},
            "recommendations": [
                "非重要タスクを一時停止",
                "不要なコンポーネントをシャットダウン",
                "データキャッシュをクリア"
            ]
        }
        
        # 安全性関連タスクのみに十分なリソースを割り当て
        for task in prioritized_tasks:
            component = task.get("component", "")
            
            if "safety" in task.get("tags", []) or component == "safety_filter":
                # 安全性コンポーネントには必要なリソースを確保
                allocation["memory"][component] = task.get("memory_required", 50)  # MB
                allocation["cpu"][component] = task.get("cpu_required", 10)  # パーセント
                allocation["tasks"][task.get("id", "unknown")] = "active"
            else:
                # その他は最小限または一時停止
                allocation["memory"][component] = min(task.get("memory_required", 50) * 0.5, 25)  # MB
                allocation["cpu"][component] = min(task.get("cpu_required", 10) * 0.5, 5)  # パーセント
                allocation["tasks"][task.get("id", "unknown")] = "suspended" if component != "self_preservation" else "active"
        
        return allocation
    
    def _warning_allocation(self, prioritized_tasks: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        リソースが警告状態での割り当て戦略
        """
        # 省エネモード - 重要タスクを優先
        allocation = {
            "memory": {},
            "cpu": {},
            "tasks": {},
            "recommendations": [
                "低優先度タスクを延期",
                "メモリ使用量の多いプロセスを最適化",
                "一時データをクリーンアップ"
            ]
        }
        
        # 優先度に応じたリソース割り当て
        remaining_memory = 100  # 単位はここでは重要でない（相対的な配分）
        remaining_cpu = 100
        
        for task in prioritized_tasks:
            component = task.get("component", "")
            priority = task.get("calculated_priority", 1)
            
            # 必要なリソース
            memory_required = task.get("memory_required", 50)
            cpu_required = task.get("cpu_required", 10)
            
            # 優先度に基づいたスケーリング
            memory_scaled = memory_required * min(priority / 5, 1)
            cpu_scaled = cpu_required * min(priority / 5, 1)
            
            # 残りリソースの確認
            if remaining_memory >= memory_scaled and remaining_cpu >= cpu_scaled:
                allocation["memory"][component] = memory_scaled
                allocation["cpu"][component] = cpu_scaled
                allocation["tasks"][task.get("id", "unknown")] = "active"
                
                remaining_memory -= memory_scaled
                remaining_cpu -= cpu_scaled
            else:
                # リソース不足の場合
                if priority >= 7:  # 高優先度タスク
                    allocation["memory"][component] = min(memory_scaled, remaining_memory)
                    allocation["cpu"][component] = min(cpu_scaled, remaining_cpu)
                    allocation["tasks"][task.get("id", "unknown")] = "active"
                    
                    remaining_memory -= allocation["memory"][component]
                    remaining_cpu -= allocation["cpu"][component]
                else:
                    # 低優先度タスクは待機状態に
                    allocation["memory"][component] = 0
                    allocation["cpu"][component] = 0
                    allocation["tasks"][task.get("id", "unknown")] = "waiting"
        
        return allocation
    
    def _normal_allocation(self, prioritized_tasks: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        通常状態でのリソース割り当て戦略
        """
        # 通常割り当て - すべてのタスクに十分なリソースを提供
        allocation = {
            "memory": {},
            "cpu": {},
            "tasks": {},
            "recommendations": []
        }
        
        for task in prioritized_tasks:
            component = task.get("component", "")
            
            # 必要なリソース（実際のシステムでは動的に計算）
            memory_required = task.get("memory_required", 50)
            cpu_required = task.get("cpu_required", 10)
            
            # 通常モードでは要求通りに割り当て
            allocation["memory"][component] = memory_required
            allocation["cpu"][component] = cpu_required
            allocation["tasks"][task.get("id", "unknown")] = "active"
        
        return allocation
