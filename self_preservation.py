import logging
import json
import os
import time
import signal
import threading
import traceback
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

class SelfPreservation:
    """
    システムの安定性維持と継続的な運用を確保するコンポーネント。
    障害検出、エラー回復、状態保存などを担当する。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        SelfPreservationの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.config = config
        self.logger = logging.getLogger("self_preservation")
        
        # システム状態
        self.system_state = "initializing"
        
        # エラーログ
        self.error_log = []
        
        # 回復戦略
        self.recovery_strategies = {
            "memory_overflow": self._recover_memory_overflow,
            "process_hang": self._recover_process_hang,
            "data_corruption": self._recover_data_corruption,
            "component_failure": self._recover_component_failure,
            "resource_exhaustion": self._recover_resource_exhaustion
        }
        
        # 監視スレッド
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # 状態保存間隔（秒）
        self.state_save_interval = 300  # 5分
        self.last_state_save = time.time()
        
        # ヘルスチェック間隔（秒）
        self.health_check_interval = 30
        
        # エラー閾値
        self.error_thresholds = {
            "consecutive_failures": 3,
            "errors_per_minute": 5,
            "critical_component_failures": 1
        }
        
        # 回復カウンター
        self.recovery_counters = {
            "total_recoveries": 0,
            "failed_recoveries": 0,
            "strategy_usage": {}
        }
        
        # コンポーネント状態
        self.component_states = {}
        
        # 安全シャットダウンフラグ
        self.shutdown_requested = False
        
        # 状態バックアップディレクトリ
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        
        self.logger.info("Self-preservation system initialized")
    
    def start_monitoring(self) -> bool:
        """
        システム監視を開始
        
        Returns:
            監視の開始が成功したかどうか
        """
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return False
        
        self.monitoring_active = True
        self.system_state = "stable"
        
        # 監視スレッドを作成
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("System monitoring started")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        システム監視を停止
        
        Returns:
            監視の停止が成功したかどうか
        """
        if not self.monitoring_active:
            self.logger.warning("Monitoring is not active")
            return False
        
        self.monitoring_active = False
        
        # スレッドが終了するのを待機
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        self.logger.info("System monitoring stopped")
        return True
    
    def register_component(self, component_name: str, initial_state: str = "active") -> None:
        """
        監視対象コンポーネントを登録
        
        Args:
            component_name: コンポーネント名
            initial_state: 初期状態
        """
        self.component_states[component_name] = {
            "state": initial_state,
            "last_heartbeat": time.time(),
            "error_count": 0,
            "recovery_count": 0,
            "last_error": None
        }
        
        self.logger.info(f"Registered component: {component_name}")
    
    def update_component_state(self, component_name: str, state: str) -> bool:
        """
        コンポーネントの状態を更新
        
        Args:
            component_name: コンポーネント名
            state: 新しい状態
            
        Returns:
            更新が成功したかどうか
        """
        if component_name not in self.component_states:
            self.logger.warning(f"Unknown component: {component_name}")
            return False
        
        previous_state = self.component_states[component_name]["state"]
        self.component_states[component_name]["state"] = state
        self.component_states[component_name]["last_heartbeat"] = time.time()
        
        # 状態変化をログに記録
        if previous_state != state:
            self.logger.info(f"Component {component_name} state changed: {previous_state} -> {state}")
            
            # エラー状態への遷移
            if state == "error" and previous_state != "error":
                self.component_states[component_name]["error_count"] += 1
                self.component_states[component_name]["last_error"] = time.time()
                
                # エラーログに追加
                self.error_log.append({
                    "component": component_name,
                    "previous_state": previous_state,
                    "timestamp": datetime.now().isoformat(),
                    "type": "component_error"
                })
                
                # 重要コンポーネントの場合、システム状態に反映
                if component_name in ["safety_filter", "main_assistant"]:
                    self._update_system_state("degraded")
        
        return True
    
    def component_heartbeat(self, component_name: str) -> bool:
        """
        コンポーネントからのハートビートを受信
        
        Args:
            component_name: コンポーネント名
            
        Returns:
            ハートビートの処理が成功したかどうか
        """
        if component_name not in self.component_states:
            self.logger.warning(f"Heartbeat from unknown component: {component_name}")
            return False
        
        self.component_states[component_name]["last_heartbeat"] = time.time()
        return True
    
    def report_error(self, error_data: Dict[str, Any]) -> str:
        """
        エラーを報告
        
        Args:
            error_data: エラー情報
            
        Returns:
            エラーID
        """
        # 必須フィールドの確認
        required_fields = ["component", "error_type", "description"]
        for field in required_fields:
            if field not in error_data:
                self.logger.warning(f"Error report missing required field: {field}")
                return ""
        
        # エラーIDの生成
        error_id = f"err_{int(time.time())}_{hash(error_data['description']) % 10000:04d}"
        
        # タイムスタンプの追加
        error_data["timestamp"] = datetime.now().isoformat()
        error_data["error_id"] = error_id
        
        # エラーログに追加
        self.error_log.append(error_data)
        
        # エラーの重大度に応じたアクション
        severity = error_data.get("severity", "warning")
        
        if severity == "critical":
            self._update_system_state("degraded")
            
            # 即時回復が必要な場合
            if error_data.get("requires_immediate_recovery", False):
                recovery_type = error_data.get("recovery_type")
                if recovery_type in self.recovery_strategies:
                    self._attempt_recovery(recovery_type, error_data)
        
        elif severity == "warning":
            # コンポーネントの状態を更新
            component = error_data["component"]
            if component in self.component_states:
                if self.component_states[component]["error_count"] >= self.error_thresholds["consecutive_failures"]:
                    self._update_system_state("degraded")
        
        self.logger.warning(f"Error reported: {error_id} - {error_data['description']}")
        return error_id
    
    def save_system_state(self) -> Dict[str, Any]:
        """
        システム状態を保存
        
        Returns:
            保存されたシステム状態情報
        """
        # 保存対象の状態情報
        state_data = {
            "timestamp": datetime.now().isoformat(),
            "system_state": self.system_state,
            "component_states": self.component_states,
            "recovery_counters": self.recovery_counters,
            "error_count": len(self.error_log)
        }
        
        # ファイル名
        filename = os.path.join(
            self.backup_dir,
            f"system_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        # 状態の保存
        try:
            with open(filename, "w") as f:
                json.dump(state_data, f, indent=2)
            
            self.last_state_save = time.time()
            self.logger.info(f"System state saved to {filename}")
            
            # 古いバックアップファイルの削除（最新10件を残す）
            self._cleanup_old_backups()
            
            return {
                "status": "success",
                "filename": filename,
                "timestamp": state_data["timestamp"]
            }
            
        except Exception as e:
            error_details = {
                "component": "self_preservation",
                "error_type": "state_save_failure",
                "description": f"Failed to save system state: {str(e)}",
                "severity": "warning",
                "exception": traceback.format_exc()
            }
            
            self.error_log.append(error_details)
            self.logger.error(f"Failed to save system state: {str(e)}")
            
            return {
                "status": "error",
                "message": str(e)
            }
    
    def restore_system_state(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        システム状態を復元
        
        Args:
            filename: 復元する状態ファイルのパス（省略時は最新）
            
        Returns:
            復元結果
        """
        # ファイル名が指定されない場合は最新のバックアップを使用
        if not filename:
            backup_files = self._get_backup_files()
            if not backup_files:
                return {
                    "status": "error",
                    "message": "No backup files found"
                }
            filename = backup_files[0]  # 最新のバックアップ
        
        # 状態の復元
        try:
            with open(filename, "r") as f:
                state_data = json.load(f)
            
            # 状態の適用
            self.system_state = state_data.get("system_state", "stable")
            self.component_states = state_data.get("component_states", {})
            self.recovery_counters = state_data.get("recovery_counters", {
                "total_recoveries": 0,
                "failed_recoveries": 0,
                "strategy_usage": {}
            })
            
            self.logger.info(f"System state restored from {filename}")
            
            return {
                "status": "success",
                "filename": filename,
                "timestamp": state_data.get("timestamp"),
                "restored_state": self.system_state
            }
            
        except Exception as e:
            error_details = {
                "component": "self_preservation",
                "error_type": "state_restore_failure",
                "description": f"Failed to restore system state: {str(e)}",
                "severity": "warning",
                "exception": traceback.format_exc()
            }
            
            self.error_log.append(error_details)
            self.logger.error(f"Failed to restore system state: {str(e)}")
            
            return {
                "status": "error",
                "message": str(e)
            }
    
    def safe_shutdown(self, reason: str = "manual") -> Dict[str, Any]:
        """
        システムの安全なシャットダウンを実行
        
        Args:
            reason: シャットダウンの理由
            
        Returns:
            シャットダウン結果
        """
        self.logger.info(f"Safe shutdown initiated. Reason: {reason}")
        
        # シャットダウンフラグを設定
        self.shutdown_requested = True
        
        # 最終状態の保存
        save_result = self.save_system_state()
        
        # 監視の停止
        if self.monitoring_active:
            self.stop_monitoring()
        
        # システム状態の更新
        self._update_system_state("shutting_down")
        
        # シャットダウンログ
        shutdown_log = {
            "component": "self_preservation",
            "event_type": "shutdown",
            "description": f"System shutdown: {reason}",
            "timestamp": datetime.now().isoformat(),
            "state_save_result": save_result.get("status")
        }
        
        self.logger.info(f"System shutdown complete")
        
        return {
            "status": "success",
            "timestamp": shutdown_log["timestamp"],
            "reason": reason,
            "state_saved": save_result.get("status") == "success"
        }
    
    def monitor_system_health(self) -> Dict[str, Any]:
        """
        システムの健全性をモニタリング
        
        Returns:
            健全性ステータス
        """
        # コンポーネントの状態チェック
        component_status = {}
        inactive_components = []
        error_components = []
        
        current_time = time.time()
        
        for component, state in self.component_states.items():
            # ハートビートのチェック
            heartbeat_age = current_time - state["last_heartbeat"]
            heartbeat_status = "ok" if heartbeat_age < 60 else "late" if heartbeat_age < 180 else "missing"
            
            component_status[component] = {
                "state": state["state"],
                "heartbeat": heartbeat_status,
                "error_count": state["error_count"],
                "last_error_age": (
                    current_time - state["last_error"] if state["last_error"] is not None else None
                )
            }
            
            # 非アクティブなコンポーネントの検出
            if heartbeat_status == "missing" or state["state"] == "inactive":
                inactive_components.append(component)
            
            # エラー状態のコンポーネントの検出
            if state["state"] == "error":
                error_components.append(component)
        
        # 最近のエラーの数
        recent_errors = 0
        for error in self.error_log:
            if "timestamp" in error:
                error_time = datetime.fromisoformat(error["timestamp"])
                age_seconds = (datetime.now() - error_time).total_seconds()
                if age_seconds < 60:  # 1分以内のエラー
                    recent_errors += 1
        
        # システム状態の判定
        system_status = "healthy"
        
        if error_components:
            system_status = "degraded"
        
        if len(error_components) > 1 or recent_errors > self.error_thresholds["errors_per_minute"]:
            system_status = "critical"
        
        # リソース使用状況（実際のシステムではリソースマネージャーと連携）
        resource_status = {
            "memory_usage": 0.5,  # ダミー値
            "cpu_usage": 0.3,     # ダミー値
            "disk_usage": 0.4     # ダミー値
        }
        
        # 健全性スコアの計算（0-100）
        health_score = 100
        
        # 非アクティブコンポーネントによる減点
        health_score -= len(inactive_components) * 15
        
        # エラーコンポーネントによる減点
        health_score -= len(error_components) * 20
        
        # 最近のエラーによる減点
        health_score -= recent_errors * 5
        
        # スコアの範囲制限
        health_score = max(0, min(100, health_score))
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "system_state": self.system_state,
            "status": system_status,
            "health_score": health_score,
            "components": component_status,
            "resources": resource_status,
            "recent_errors": recent_errors,
            "inactive_components": inactive_components,
            "error_components": error_components
        }
        
        # システム状態の更新
        if self.system_state != "shutting_down":
            if system_status == "critical" and self.system_state != "critical":
                self._update_system_state("critical")
            elif system_status == "degraded" and self.system_state == "stable":
                self._update_system_state("degraded")
            elif system_status == "healthy" and self.system_state != "stable":
                self._update_system_state("stable")
        
        return health_status
    
    def implement_failsafe(self, error_condition: str) -> Dict[str, Any]:
        """
        エラー状態に対するフェイルセーフを実装
        
        Args:
            error_condition: エラー状態の種類
            
        Returns:
            実装されたフェイルセーフ戦略
        """
        self.logger.info(f"Implementing failsafe for error condition: {error_condition}")
        
        # エラー条件に応じた戦略
        if error_condition == "memory_overflow":
            strategy = {
                "action": "clear_caches",
                "priority": 1,
                "fallback": "reduce_processing"
            }
            
            # キャッシュクリアのシミュレーション
            success = True  # 実際のシステムでは実際のアクションの結果
            
            if success:
                self.logger.info("Implemented failsafe: cleared caches")
            else:
                self.logger.warning("Failsafe action failed, using fallback: reduce processing")
                strategy["action"] = strategy["fallback"]
        
        elif error_condition == "component_failure":
            strategy = {
                "action": "restart_component",
                "priority": 3,
                "fallback": "isolate_component"
            }
            
            # コンポーネント再起動のシミュレーション
            success = True  # 実際のシステムでは実際のアクションの結果
            
            if success:
                self.logger.info("Implemented failsafe: restarted failed component")
            else:
                self.logger.warning("Failsafe action failed, using fallback: isolate component")
                strategy["action"] = strategy["fallback"]
        
        elif error_condition == "data_corruption":
            strategy = {
                "action": "restore_backup",
                "priority": 2,
                "fallback": "initialize_subsystem"
            }
            
            # バックアップ復元のシミュレーション
            success = self.restore_system_state().get("status") == "success"
            
            if success:
                self.logger.info("Implemented failsafe: restored from backup")
            else:
                self.logger.warning("Failsafe action failed, using fallback: initialize subsystem")
                strategy["action"] = strategy["fallback"]
        
        elif error_condition == "resource_exhaustion":
            strategy = {
                "action": "throttle_processing",
                "priority": 2,
                "fallback": "terminate_low_priority"
            }
            
            # 処理スロットリングのシミュレーション
            success = True  # 実際のシステムでは実際のアクションの結果
            
            if success:
                self.logger.info("Implemented failsafe: throttled processing")
            else:
                self.logger.warning("Failsafe action failed, using fallback: terminate low priority tasks")
                strategy["action"] = strategy["fallback"]
        
        else:
            strategy = {
                "action": "log_and_notify",
                "priority": 1,
                "fallback": None
            }
            self.logger.warning(f"Unknown error condition: {error_condition}")
        
        # 実行結果
        result = {
            "error_condition": error_condition,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat(),
            "success": success
        }
        
        return result
    
    def _monitoring_loop(self) -> None:
        """
        システム監視ループ
        """
        self.logger.info("Monitoring loop started")
        
        while self.monitoring_active:
            try:
                # ヘルスチェック
                health_status = self.monitor_system_health()
                
                # 重大な状態の場合は回復を試みる
                if health_status["status"] == "critical":
                    self._attempt_recovery_from_health_status(health_status)
                
                # 定期的な状態保存
                if time.time() - self.last_state_save >= self.state_save_interval:
                    self.save_system_state()
                
                # エラーログのクリーンアップ
                if len(self.error_log) > 1000:
                    self.error_log = self.error_log[-1000:]
                
                # 休止
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                error_details = {
                    "component": "self_preservation",
                    "error_type": "monitoring_error",
                    "description": f"Error in monitoring loop: {str(e)}",
                    "severity": "warning",
                    "exception": traceback.format_exc()
                }
                self.error_log.append(error_details)
                
                # 短い休止の後に再試行
                time.sleep(5)
    
    def _update_system_state(self, new_state: str) -> None:
        """
        システム状態を更新
        """
        old_state = self.system_state
        self.system_state = new_state
        
        if old_state != new_state:
            self.logger.info(f"System state changed: {old_state} -> {new_state}")
            
            # 状態変化イベントをログに記録
            event = {
                "component": "self_preservation",
                "event_type": "state_change",
                "description": f"System state changed from {old_state} to {new_state}",
                "timestamp": datetime.now().isoformat()
            }
            self.error_log.append(event)
    
    def _attempt_recovery_from_health_status(self, health_status: Dict[str, Any]) -> None:
        """
        ヘルスステータスに基づいて回復を試みる
        """
        # エラー状態のコンポーネントに対する回復
        for component in health_status.get("error_components", []):
            self.logger.info(f"Attempting recovery for component: {component}")
            
            # 回復戦略の選択
            recovery_type = "component_failure"
            
            # 特定のコンポーネントに特化した回復戦略
            if component == "safety_filter":
                # 安全フィルタは重要なのでより積極的な回復
                recovery_type = "critical_component_failure"
            
            # 回復の試み
            if recovery_type in self.recovery_strategies:
                self._attempt_recovery(recovery_type, {"component": component})
    
    def _attempt_recovery(self, recovery_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        特定のリカバリー戦略を試みる
        """
        self.logger.info(f"Attempting recovery strategy: {recovery_type}")
        
        # 回復カウンターの更新
        self.recovery_counters["total_recoveries"] += 1
        
        if recovery_type not in self.recovery_counters["strategy_usage"]:
            self.recovery_counters["strategy_usage"][recovery_type] = 1
        else:
            self.recovery_counters["strategy_usage"][recovery_type] += 1
        
        # 戦略の実行
        try:
            if recovery_type in self.recovery_strategies:
                result = self.recovery_strategies[recovery_type](context)
                
                if result.get("success", False):
                    self.logger.info(f"Recovery successful: {recovery_type}")
                else:
                    self.logger.warning(f"Recovery failed: {recovery_type}")
                    self.recovery_counters["failed_recoveries"] += 1
                
                return result
            else:
                self.logger.warning(f"Unknown recovery strategy: {recovery_type}")
                self.recovery_counters["failed_recoveries"] += 1
                
                return {
                    "recovery_type": recovery_type,
                    "success": False,
                    "message": "Unknown recovery strategy"
                }
                
        except Exception as e:
            self.logger.error(f"Error during recovery attempt: {str(e)}")
            self.recovery_counters["failed_recoveries"] += 1
            
            return {
                "recovery_type": recovery_type,
                "success": False,
                "message": f"Recovery error: {str(e)}",
                "exception": traceback.format_exc()
            }
    
    def _recover_memory_overflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        メモリオーバーフローからの回復
        """
        # これは簡略化された実装
        # 実際のシステムではより洗練された回復メカニズムを使用
        
        self.logger.info("Executing memory overflow recovery strategy")
        
        # 回復アクション（実際のシステムではガベージコレクションなど）
        success = True  # 実際のシステムでは実際のアクションの結果
        
        return {
            "recovery_type": "memory_overflow",
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["clear_caches", "force_garbage_collection"]
        }
    
    def _recover_process_hang(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        プロセスハングからの回復
        """
        # これは簡略化された実装
        self.logger.info("Executing process hang recovery strategy")
        
        # 回復アクション（実際のシステムではプロセス再起動など）
        success = True  # 実際のシステムでは実際のアクションの結果
        
        return {
            "recovery_type": "process_hang",
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["timeout_reset", "process_restart"]
        }
    
    def _recover_data_corruption(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        データ破損からの回復
        """
        # これは簡略化された実装
        self.logger.info("Executing data corruption recovery strategy")
        
        # 回復アクション（実際のシステムではバックアップからの復元など）
        success = True  # 実際のシステムでは実際のアクションの結果
        
        return {
            "recovery_type": "data_corruption",
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["restore_from_backup", "validate_data_integrity"]
        }
    
    def _recover_component_failure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        コンポーネント障害からの回復
        """
        # これは簡略化された実装
        self.logger.info("Executing component failure recovery strategy")
        
        component = context.get("component", "unknown")
        
        # コンポーネントの状態をリセット
        if component in self.component_states:
            self.component_states[component]["state"] = "restarting"
            self.component_states[component]["last_heartbeat"] = time.time()
        
        # 回復アクション（実際のシステムではコンポーネント再起動など）
        success = True  # 実際のシステムでは実際のアクションの結果
        
        # 回復成功の場合、コンポーネントの状態を更新
        if success and component in self.component_states:
            self.component_states[component]["state"] = "active"
            self.component_states[component]["recovery_count"] += 1
        
        return {
            "recovery_type": "component_failure",
            "component": component,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["restart_component", "verify_functionality"]
        }
    
    def _recover_resource_exhaustion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        リソース枯渇からの回復
        """
        # これは簡略化された実装
        self.logger.info("Executing resource exhaustion recovery strategy")
        
        # 回復アクション（実際のシステムではリソース解放など）
        success = True  # 実際のシステムでは実際のアクションの結果
        
        return {
            "recovery_type": "resource_exhaustion",
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["release_unused_resources", "prioritize_essential_tasks"]
        }
    
    def _get_backup_files(self) -> List[str]:
        """
        バックアップファイルのリストを取得（新しい順）
        """
        if not os.path.exists(self.backup_dir):
            return []
        
        files = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("system_state_") and f.endswith(".json")
        ]
        
        # 更新日時でソート（新しい順）
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        return files
    
    def _cleanup_old_backups(self) -> None:
        """
        古いバックアップファイルをクリーンアップ（最新10件を残す）
        """
        files = self._get_backup_files()
        
        # 10件より多い場合、古いファイルを削除
        if len(files) > 10:
            for file_to_delete in files[10:]:
                try:
                    os.remove(file_to_delete)
                    self.logger.debug(f"Deleted old backup: {file_to_delete}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete old backup {file_to_delete}: {str(e)}")
