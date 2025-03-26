import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

# テスト対象のモジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goal_manager import GoalManager

class TestGoalManager(unittest.TestCase):
    """GoalManagerのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 設定ファイルのモックを作成
        self.mock_config = {
            "self_improvement": {
                "allowed": True,
                "scope": "bounded",
                "requires_review": True,
                "improvement_areas": [
                    "knowledge_base",
                    "response_quality",
                    "reasoning_process"
                ]
            }
        }
        
        # open関数をパッチしてモック設定を返すようにする
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.mock_config))):
            self.goal_manager = GoalManager()
    
    def test_initialization(self):
        """初期化が正しく行われることを確認"""
        self.assertEqual(len(self.goal_manager.goals), 0)
        self.assertEqual(len(self.goal_manager.priorities), 0)
        self.assertEqual(len(self.goal_manager.progress), 0)
        self.assertEqual(len(self.goal_manager.goal_history), 0)
        
        # 許可された改善領域が正しくロードされることを確認
        expected_areas = ["knowledge_base", "response_quality", "reasoning_process"]
        self.assertEqual(self.goal_manager.allowed_improvement_areas, expected_areas)
    
    def test_set_goal(self):
        """目標設定機能のテスト"""
        # 有効な領域で目標を設定
        goal_id = self.goal_manager.set_goal("knowledge_base", "テスト目標", 3)
        
        # 目標IDが生成されることを確認
        self.assertIsNotNone(goal_id)
        
        # 目標が正しく追加されることを確認
        self.assertEqual(len(self.goal_manager.goals), 1)
        self.assertEqual(self.goal_manager.goals[0]["description"], "テスト目標")
        self.assertEqual(self.goal_manager.goals[0]["area"], "knowledge_base")
        self.assertEqual(self.goal_manager.goals[0]["priority"], 3)
        self.assertEqual(self.goal_manager.goals[0]["status"], "active")
        
        # 優先度と進捗が正しく設定されることを確認
        self.assertEqual(self.goal_manager.priorities[goal_id], 3)
        self.assertEqual(self.goal_manager.progress[goal_id], 0)
        
        # 履歴に記録されることを確認
        self.assertEqual(len(self.goal_manager.goal_history), 1)
        self.assertEqual(self.goal_manager.goal_history[0]["event"], "goal_created")
        self.assertEqual(self.goal_manager.goal_history[0]["goal_id"], goal_id)
    
    def test_invalid_area(self):
        """無効な領域での目標設定が失敗することを確認"""
        goal_id = self.goal_manager.set_goal("invalid_area", "無効な目標", 3)
        
        # 無効な領域の場合はNoneが返されることを確認
        self.assertIsNone(goal_id)
        
        # 目標が追加されないことを確認
        self.assertEqual(len(self.goal_manager.goals), 0)
    
    def test_update_goal_progress(self):
        """目標進捗の更新機能のテスト"""
        # 目標を設定
        goal_id = self.goal_manager.set_goal("reasoning_process", "進捗テスト", 2)
        
        # 進捗を更新
        result = self.goal_manager.update_goal_progress(goal_id, 50)
        
        # 更新が成功することを確認
        self.assertTrue(result)
        
        # 進捗が正しく更新されることを確認
        self.assertEqual(self.goal_manager.progress[goal_id], 50)
        
        # 履歴に記録されることを確認
        self.assertEqual(len(self.goal_manager.goal_history), 2)  # 作成と更新
        self.assertEqual(self.goal_manager.goal_history[1]["event"], "progress_updated")
        self.assertEqual(self.goal_manager.goal_history[1]["goal_id"], goal_id)
        self.assertEqual(self.goal_manager.goal_history[1]["previous"], 0)
        self.assertEqual(self.goal_manager.goal_history[1]["current"], 50)
    
    def test_goal_completion(self):
        """目標完了処理のテスト"""
        # 目標を設定
        goal_id = self.goal_manager.set_goal("response_quality", "完了テスト", 1)
        
        # 進捗を100%に更新
        result = self.goal_manager.update_goal_progress(goal_id, 100)
        
        # 更新が成功することを確認
        self.assertTrue(result)
        
        # 目標のステータスが完了に変わることを確認
        goal = next((g for g in self.goal_manager.goals if g["id"] == goal_id), None)
        self.assertEqual(goal["status"], "completed")
        
        # 履歴に完了イベントが記録されることを確認
        self.assertEqual(len(self.goal_manager.goal_history), 3)  # 作成、更新、完了
        self.assertEqual(self.goal_manager.goal_history[2]["event"], "goal_completed")
        self.assertEqual(self.goal_manager.goal_history[2]["goal_id"], goal_id)
    
    def test_create_learning_plan(self):
        """学習計画作成機能のテスト"""
        # 目標を設定
        goal_id = self.goal_manager.set_goal("knowledge_base", "計画テスト", 3)
        
        # 学習計画を作成
        plan = self.goal_manager.create_learning_plan(goal_id)
        
        # 計画が作成されることを確認
        self.assertIsNotNone(plan)
        self.assertEqual(plan["goal_id"], goal_id)
        self.assertEqual(plan["objective"], "計画テスト")
        
        # 学習計画の内容を確認
        self.assertIn("metrics", plan)
        self.assertIn("actions", plan)
        self.assertIn("coverage_increase", plan["metrics"])
        self.assertEqual(len(plan["actions"]), 4)  # 4つのアクションが含まれる
    
    def test_get_active_goals(self):
        """アクティブな目標取得機能のテスト"""
        # 複数の目標を設定
        goal_id1 = self.goal_manager.set_goal("knowledge_base", "目標1", 2)
        goal_id2 = self.goal_manager.set_goal("response_quality", "目標2", 4)
        goal_id3 = self.goal_manager.set_goal("reasoning_process", "目標3", 1)
        
        # 一つの目標を完了状態に
        self.goal_manager.update_goal_progress(goal_id1, 100)
        
        # アクティブな目標を取得
        active_goals = self.goal_manager.get_active_goals()
        
        # アクティブな目標が2つあることを確認
        self.assertEqual(len(active_goals), 2)
        
        # 優先度順にソートされていることを確認
        self.assertEqual(active_goals[0]["id"], goal_id2)  # 優先度4
        self.assertEqual(active_goals[1]["id"], goal_id3)  # 優先度1
    
    def test_identify_growth_needs(self):
        """成長ニーズ特定機能のテスト"""
        # モックコンテキストの作成
        mock_context = {
            "session_history": [
                {"role": "user", "content": "What is machine learning?"},
                {"role": "assistant", "content": "Machine learning is..."},
                {"role": "user", "content": "How does neural network work?"},
                {"role": "assistant", "content": "Neural networks are..."},
                {"role": "user", "content": "Why is deep learning effective?"},
                {"role": "assistant", "content": "Deep learning is effective because..."}
            ],
            "learned_preferences": {
                "response_length": "detailed",
                "include_examples": True
            }
        }
        
        # 成長ニーズを特定
        needs = self.goal_manager.identify_growth_needs(mock_context)
        
        # 少なくとも2つのニーズが特定されることを確認
        self.assertGreaterEqual(len(needs), 2)
        
        # 説明的な質問に対する推論能力向上のニーズが含まれることを確認
        reasoning_need = next((n for n in needs if n["area"] == "reasoning_process"), None)
        self.assertIsNotNone(reasoning_need)
        
        # 詳細な情報提供のための知識拡張のニーズが含まれることを確認
        knowledge_need = next((n for n in needs if n["area"] == "knowledge_base" and "詳細な情報" in n["description"]), None)
        self.assertIsNotNone(knowledge_need)

if __name__ == '__main__':
    unittest.main()
