import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json

# テスト対象のモジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self_feedback import SelfFeedbackSystem

class TestSelfFeedbackSystem(unittest.TestCase):
    """SelfFeedbackSystemのテストクラス"""
    
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
            self.feedback_system = SelfFeedbackSystem()
    
    def test_initialization(self):
        """初期化が正しく行われることを確認"""
        self.assertEqual(len(self.feedback_system.evaluation_history), 0)
        self.assertIsNotNone(self.feedback_system.adjustment_parameters)
        
        # 品質基準が正しく設定されることを確認
        self.assertGreater(self.feedback_system.quality_thresholds["relevance"], 0)
        self.assertGreater(self.feedback_system.quality_thresholds["clarity"], 0)
        
        # 許可された改善領域が正しくロードされることを確認
        expected_areas = ["knowledge_base", "response_quality", "reasoning_process"]
        self.assertEqual(self.feedback_system.allowed_improvement_areas, expected_areas)
    
    def test_evaluate_response_relevance(self):
        """応答の関連性評価のテスト"""
        # テスト用の応答とクエリ
        query = "What is artificial intelligence?"
        response = "Artificial intelligence refers to systems that can perform tasks that typically require human intelligence. These include learning, reasoning, problem-solving, perception, and language understanding."
        context = {}
        
        # 応答を評価
        evaluation = self.feedback_system.evaluate_response(response, context, query)
        
        # 評価結果が正しい形式であることを確認
        self.assertIn("relevance", evaluation)
        self.assertIn("clarity", evaluation)
        self.assertIn("precision", evaluation)
        self.assertIn("depth", evaluation)
        self.assertIn("coherence", evaluation)
        self.assertIn("overall_score", evaluation)
        
        # 関連性スコアが高いことを確認（クエリのキーワードが応答に含まれるため）
        self.assertGreater(evaluation["relevance"], 0.5)
        
        # 履歴に記録されることを確認
        self.assertEqual(len(self.feedback_system.evaluation_history), 1)
    
    def test_evaluate_response_clarity(self):
        """応答の明確さ評価のテスト"""
        # 明確な応答
        clear_response = "Machine learning is a field of AI that focuses on building systems that learn from data. It has three main types: supervised, unsupervised, and reinforcement learning."
        
        # 不明確な応答（複雑で冗長）
        unclear_response = "The paradigmatic instantiation of computational methodologies which endeavor to ascertain algorithmic patterns within multidimensional datasets, thereby facilitating predictive extrapolations through parameterized mathematical constructs, is fundamentally predicated upon the epistemological framework of empirical learning mechanisms, which themselves are categorized into tripartite taxonomical classifications based on the supervisory modality of the learning process, each with their own distinctive characteristics and operational methodologies."
        
        # 明確な応答の評価
        clear_eval = self.feedback_system.evaluate_response(clear_response, {}, "What is machine learning?")
        
        # 不明確な応答の評価
        unclear_eval = self.feedback_system.evaluate_response(unclear_response, {}, "What is machine learning?")
        
        # 明確な応答の方が明確さスコアが高いことを確認
        self.assertGreater(clear_eval["clarity"], unclear_eval["clarity"])
    
    def test_evaluate_response_depth(self):
        """応答の深さ評価のテスト"""
        # 浅い応答
        shallow_response = "Neural networks are AI systems."
        
        # 深い応答
        deep_response = "Neural networks are computational models inspired by the human brain's structure. They consist of layers of interconnected nodes or 'neurons' that process information. These networks learn patterns in data through a process called training, where connection weights are adjusted based on error feedback. This architecture allows them to handle complex problems in image recognition, natural language processing, and other domains. The depth of a neural network refers to the number of layers, with 'deep learning' involving networks with many layers, which can capture hierarchical representations of data."
        
        # 浅い応答の評価
        shallow_eval = self.feedback_system.evaluate_response(shallow_response, {}, "Explain neural networks")
        
        # 深い応答の評価
        deep_eval = self.feedback_system.evaluate_response(deep_response, {}, "Explain neural networks")
        
        # 深い応答の方が深さスコアが高いことを確認
        self.assertGreater(deep_eval["depth"], shallow_eval["depth"])
    
    def test_adjust_parameters(self):
        """パラメータ調整機能のテスト"""
        # 低品質の評価メトリクス
        low_metrics = {
            "relevance": 0.5,  # 閾値以下
            "clarity": 0.5,    # 閾値以下
            "precision": 0.9,
            "depth": 0.4,      # 閾値以下
            "coherence": 0.8,
            "overall_score": 0.6
        }
        
        # パラメータ調整前の値を保存
        original_context_level = self.feedback_system.adjustment_parameters["context_consideration_level"]
        original_clarity_weight = self.feedback_system.adjustment_parameters["clarity_weight"]
        original_depth_weight = self.feedback_system.adjustment_parameters["depth_weight"]
        
        # パラメータ調整
        adjustments = self.feedback_system.adjust_parameters(low_metrics)
        
        # 調整が行われたことを確認
        self.assertIn("parameters", adjustments)
        self.assertIn("reasoning", adjustments)
        
        # 関連性が低いため、コンテキスト考慮レベルが上がったことを確認
        self.assertIn("context_consideration_level", adjustments["parameters"])
        self.assertGreater(
            self.feedback_system.adjustment_parameters["context_consideration_level"],
            original_context_level
        )
        
        # 明確さが低いため、明確さの重みが上がったことを確認
        self.assertIn("clarity_weight", adjustments["parameters"])
        self.assertGreater(
            self.feedback_system.adjustment_parameters["clarity_weight"],
            original_clarity_weight
        )
        
        # 深さが低いため、深さの重みが上がったことを確認
        self.assertIn("depth_weight", adjustments["parameters"])
        self.assertGreater(
            self.feedback_system.adjustment_parameters["depth_weight"],
            original_depth_weight
        )
    
    def test_generate_improvement_suggestions(self):
        """改善提案生成機能のテスト"""
        # 評価履歴が少ない場合は提案が生成されないことを確認
        suggestions = self.feedback_system.generate_improvement_suggestions()
        self.assertEqual(len(suggestions), 0)
        
        # 評価履歴を追加
        for i in range(20):
            # 明確さの低い評価を多数作成
            self.feedback_system.evaluation_history.append({
                "metrics": {
                    "relevance": 0.9,
                    "clarity": 0.5,  # 明確さが低い
                    "precision": 0.8,
                    "depth": 0.7,
                    "coherence": 0.8,
                    "overall_score": 0.7
                },
                "response_excerpt": "Test response",
                "query_excerpt": "Test query"
            })
        
        # 改善提案を生成
        suggestions = self.feedback_system.generate_improvement_suggestions()
        
        # 提案が生成されることを確認
        self.assertGreater(len(suggestions), 0)
        
        # 明確さに関する提案が含まれることを確認
        clarity_suggestion = next((s for s in suggestions if "明確さ" in s["description"] or "表現" in s["description"]), None)
        self.assertIsNotNone(clarity_suggestion)
        
        # 提案が許可された改善領域に含まれることを確認
        self.assertIn(clarity_suggestion["area"], self.feedback_system.allowed_improvement_areas)

if __name__ == '__main__':
    unittest.main()
