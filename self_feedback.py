import logging
from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime

class SelfFeedbackSystem:
    """
    自己評価と調整のためのフィードバックループシステム。
    出力の質を自己分析し、内部パラメータを自動調整する。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        SelfFeedbackSystemの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.config = config.get("self_improvement", {})
        self.logger = logging.getLogger("self_feedback")
        
        # 自己評価の履歴
        self.evaluation_history = []
        
        # 調整パラメータ
        self.adjustment_parameters = {
            "relevance_weight": 1.0,
            "clarity_weight": 1.0,
            "precision_weight": 1.0,
            "depth_weight": 1.0,
            "response_length_multiplier": 1.0,
            "context_consideration_level": 1.0
        }
        
        # 許可された改善領域
        self.allowed_improvement_areas = self.config.get("improvement_areas", [
            "knowledge_base",
            "response_quality",
            "reasoning_process"
        ])
        
        # 品質基準の閾値
        self.quality_thresholds = {
            "relevance": 0.7,
            "clarity": 0.7,
            "precision": 0.8,
            "depth": 0.6,
            "coherence": 0.75
        }
        
        self.logger.info("Self-feedback system initialized")
    
    def evaluate_response(self, response: str, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        応答の質を自己評価する
        
        Args:
            response: 評価対象の応答
            context: 会話コンテキスト
            query: ユーザーのクエリ
            
        Returns:
            評価メトリクス
        """
        metrics = {
            "relevance": self._calculate_relevance(response, query),
            "clarity": self._calculate_clarity(response),
            "precision": self._calculate_precision(response),
            "depth": self._calculate_depth(response, query),
            "coherence": self._calculate_coherence(response),
            "timestamp": datetime.now().isoformat()
        }
        
        # 全体スコアの計算
        metrics["overall_score"] = (
            metrics["relevance"] * self.adjustment_parameters["relevance_weight"] +
            metrics["clarity"] * self.adjustment_parameters["clarity_weight"] +
            metrics["precision"] * self.adjustment_parameters["precision_weight"] +
            metrics["depth"] * self.adjustment_parameters["depth_weight"]
        ) / sum([
            self.adjustment_parameters["relevance_weight"],
            self.adjustment_parameters["clarity_weight"],
            self.adjustment_parameters["precision_weight"],
            self.adjustment_parameters["depth_weight"]
        ])
        
        # 履歴に追加
        evaluation_record = {
            "metrics": metrics,
            "response_excerpt": response[:100] + "..." if len(response) > 100 else response,
            "query_excerpt": query[:100] + "..." if len(query) > 100 else query
        }
        self.evaluation_history.append(evaluation_record)
        
        self.logger.info(f"Response evaluated with overall score: {metrics['overall_score']:.2f}")
        return metrics
    
    def adjust_parameters(self, evaluation_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        評価メトリクスに基づいて内部パラメータを調整
        
        Args:
            evaluation_metrics: 応答評価メトリクス
            
        Returns:
            調整されたパラメータと調整根拠
        """
        adjustments = {
            "parameters": {},
            "reasoning": {}
        }
        
        # 関連性の改善
        if evaluation_metrics["relevance"] < self.quality_thresholds["relevance"]:
            # コンテキスト考慮レベルを上げる
            old_value = self.adjustment_parameters["context_consideration_level"]
            self.adjustment_parameters["context_consideration_level"] = min(
                old_value * 1.1, 2.0  # 上限
            )
            
            adjustments["parameters"]["context_consideration_level"] = {
                "old": old_value,
                "new": self.adjustment_parameters["context_consideration_level"]
            }
            
            adjustments["reasoning"]["context_consideration_level"] = (
                f"関連性スコア({evaluation_metrics['relevance']:.2f})が閾値({self.quality_thresholds['relevance']})を"
                f"下回ったため、コンテキスト考慮レベルを増加"
            )
        
        # 明確さの改善
        if evaluation_metrics["clarity"] < self.quality_thresholds["clarity"]:
            # 明確さの重みを上げる
            old_value = self.adjustment_parameters["clarity_weight"]
            self.adjustment_parameters["clarity_weight"] = min(
                old_value * 1.15, 2.0  # 上限
            )
            
            adjustments["parameters"]["clarity_weight"] = {
                "old": old_value,
                "new": self.adjustment_parameters["clarity_weight"]
            }
            
            adjustments["reasoning"]["clarity_weight"] = (
                f"明確さスコア({evaluation_metrics['clarity']:.2f})が閾値({self.quality_thresholds['clarity']})を"
                f"下回ったため、明確さの重みを増加"
            )
        
        # 深さの改善
        if evaluation_metrics["depth"] < self.quality_thresholds["depth"]:
            # 応答長の乗数を上げる
            old_value = self.adjustment_parameters["response_length_multiplier"]
            self.adjustment_parameters["response_length_multiplier"] = min(
                old_value * 1.1, 1.5  # 上限
            )
            
            adjustments["parameters"]["response_length_multiplier"] = {
                "old": old_value,
                "new": self.adjustment_parameters["response_length_multiplier"]
            }
            
            # 深さの重みも上げる
            old_value = self.adjustment_parameters["depth_weight"]
            self.adjustment_parameters["depth_weight"] = min(
                old_value * 1.1, 1.5  # 上限
            )
            
            adjustments["parameters"]["depth_weight"] = {
                "old": old_value,
                "new": self.adjustment_parameters["depth_weight"]
            }
            
            adjustments["reasoning"]["depth_related"] = (
                f"深さスコア({evaluation_metrics['depth']:.2f})が閾値({self.quality_thresholds['depth']})を"
                f"下回ったため、深さの重みと応答長の乗数を増加"
            )
        
        self.logger.info(f"Parameters adjusted based on evaluation metrics")
        return adjustments
    
    def generate_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        評価履歴に基づいて改善提案を生成
        
        Returns:
            改善提案のリスト
        """
        if len(self.evaluation_history) < 5:
            # 十分なデータがない場合
            return []
        
        suggestions = []
        
        # 最近のN件の評価を分析
        recent_evaluations = self.evaluation_history[-20:]
        avg_metrics = {
            "relevance": sum(e["metrics"]["relevance"] for e in recent_evaluations) / len(recent_evaluations),
            "clarity": sum(e["metrics"]["clarity"] for e in recent_evaluations) / len(recent_evaluations),
            "precision": sum(e["metrics"]["precision"] for e in recent_evaluations) / len(recent_evaluations),
            "depth": sum(e["metrics"]["depth"] for e in recent_evaluations) / len(recent_evaluations),
            "coherence": sum(e["metrics"]["coherence"] for e in recent_evaluations) / len(recent_evaluations),
            "overall_score": sum(e["metrics"]["overall_score"] for e in recent_evaluations) / len(recent_evaluations)
        }
        
        # 最も弱い領域を特定
        weakest_area = min(
            ["relevance", "clarity", "precision", "depth", "coherence"],
            key=lambda k: avg_metrics[k]
        )
        
        # 領域別の提案
        if weakest_area == "relevance" and "response_quality" in self.allowed_improvement_areas:
            suggestions.append({
                "area": "response_quality",
                "description": "関連性向上のための応答生成アルゴリズムの改良",
                "metrics": {"current_score": avg_metrics["relevance"]},
                "priority": self._calculate_priority(avg_metrics["relevance"], self.quality_thresholds["relevance"])
            })
        
        elif weakest_area == "clarity" and "response_quality" in self.allowed_improvement_areas:
            suggestions.append({
                "area": "response_quality",
                "description": "明確さ向上のための表現最適化",
                "metrics": {"current_score": avg_metrics["clarity"]},
                "priority": self._calculate_priority(avg_metrics["clarity"], self.quality_thresholds["clarity"])
            })
        
        elif weakest_area == "precision" and "knowledge_base" in self.allowed_improvement_areas:
            suggestions.append({
                "area": "knowledge_base",
                "description": "精度向上のための知識ベース拡充",
                "metrics": {"current_score": avg_metrics["precision"]},
                "priority": self._calculate_priority(avg_metrics["precision"], self.quality_thresholds["precision"])
            })
        
        elif weakest_area == "depth" and "knowledge_base" in self.allowed_improvement_areas:
            suggestions.append({
                "area": "knowledge_base",
                "description": "深さ向上のための専門知識の強化",
                "metrics": {"current_score": avg_metrics["depth"]},
                "priority": self._calculate_priority(avg_metrics["depth"], self.quality_thresholds["depth"])
            })
        
        elif weakest_area == "coherence" and "reasoning_process" in self.allowed_improvement_areas:
            suggestions.append({
                "area": "reasoning_process",
                "description": "一貫性向上のための推論プロセスの改善",
                "metrics": {"current_score": avg_metrics["coherence"]},
                "priority": self._calculate_priority(avg_metrics["coherence"], self.quality_thresholds["coherence"])
            })
        
        self.logger.info(f"Generated {len(suggestions)} improvement suggestions")
        return suggestions
    
    def _calculate_relevance(self, response: str, query: str) -> float:
        """
        応答とクエリの関連性を計算
        """
        # これは簡略化された実装
        # 実際のシステムではより高度なNLPと意味解析を使用
        
        # クエリとレスポンスを単語に分解
        query_words = set(self._tokenize(query.lower()))
        response_words = set(self._tokenize(response.lower()))
        
        # 重複単語の割合を計算
        if not query_words:
            return 0.5  # デフォルト値
            
        overlap = query_words.intersection(response_words)
        relevance_score = len(overlap) / len(query_words)
        
        # 特定のキーフレーズの存在も考慮
        query_key_phrases = self._extract_key_phrases(query)
        for phrase in query_key_phrases:
            if phrase.lower() in response.lower():
                relevance_score += 0.1  # ボーナス
        
        return min(relevance_score, 1.0)  # 1.0を上限とする
    
    def _calculate_clarity(self, response: str) -> float:
        """
        応答の明確さを計算
        """
        # これは簡略化された実装
        # 実際のシステムではより高度な自然言語理解を使用
        
        # 文の平均長さ（短すぎず長すぎない文が好ましい）
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.5  # デフォルト値
        
        avg_sentence_length = sum(len(self._tokenize(s)) for s in sentences) / len(sentences)
        
        # 理想的な文の長さを15-20単語と仮定
        sentence_length_score = 1.0 - min(abs(avg_sentence_length - 17.5) / 10.0, 1.0)
        
        # 専門用語や複雑な表現の少なさも明確さに寄与
        complex_terms_count = sum(1 for word in self._tokenize(response.lower()) if len(word) > 12)
        complex_terms_ratio = complex_terms_count / max(len(self._tokenize(response)), 1)
        complexity_score = 1.0 - min(complex_terms_ratio * 10, 1.0)
        
        # 構造化された表現（箇条書きなど）の存在
        structure_score = 0.0
        if ":" in response or "-" in response or "*" in response or any(str(i)+"." in response for i in range(1, 10)):
            structure_score = 0.1
        
        clarity_score = (sentence_length_score * 0.5) + (complexity_score * 0.4) + structure_score
        return min(clarity_score, 1.0)
    
    def _calculate_precision(self, response: str) -> float:
        """
        応答の精度を計算
        """
        # これは簡略化された実装
        # 実際のシステムではより高度な事実検証を使用
        
        # 曖昧表現のカウント（低い方が良い）
        ambiguous_phrases = ["maybe", "perhaps", "might", "could be", "possibly", "一部", "場合によっては", "かもしれない"]
        ambiguity_count = sum(response.lower().count(phrase) for phrase in ambiguous_phrases)
        ambiguity_score = 1.0 - min(ambiguity_count * 0.1, 0.5)  # 最大0.5のペナルティ
        
        # 具体的な情報の存在（高い方が良い）
        concrete_indicators = [
            r'\d+\.?\d*',  # 数字
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 日付
            r'[A-Z][a-z]+ [A-Z][a-z]+',  # 固有名詞（英語）
            r'「.+」',  # 引用符（日本語）
            r'"[^"]+"',  # 引用符（英語）
        ]
        
        concreteness_count = sum(len(re.findall(pattern, response)) for pattern in concrete_indicators)
        concreteness_score = min(concreteness_count * 0.05, 0.5)  # 最大0.5のボーナス
        
        precision_score = 0.5 + ambiguity_score + concreteness_score  # ベース0.5から調整
        return min(precision_score, 1.0)
    
    def _calculate_depth(self, response: str, query: str) -> float:
        """
        応答の深さを計算
        """
        # これは簡略化された実装
        # 実際のシステムではより高度なコンテンツ分析を使用
        
        # 応答の長さ（長い方が詳細である可能性が高い）
        response_length = len(self._tokenize(response))
        length_score = min(response_length / 100, 0.5)  # 最大0.5のボーナス
        
        # 説明的なフレーズの存在
        explanation_phrases = ["because", "therefore", "as a result", "which means", "in other words", "なぜなら", "したがって", "つまり"]
        explanation_count = sum(response.lower().count(phrase) for phrase in explanation_phrases)
        explanation_score = min(explanation_count * 0.1, 0.3)  # 最大0.3のボーナス
        
        # 複数の観点からの分析
        perspective_phrases = ["however", "on the other hand", "alternatively", "in contrast", "一方で", "他方", "別の見方をすれば"]
        perspective_count = sum(response.lower().count(phrase) for phrase in perspective_phrases)
        perspective_score = min(perspective_count * 0.1, 0.2)  # 最大0.2のボーナス
        
        depth_score = length_score + explanation_score + perspective_score
        return min(depth_score, 1.0)
    
    def _calculate_coherence(self, response: str) -> float:
        """
        応答の一貫性を計算
        """
        # これは簡略化された実装
        # 実際のシステムではより高度なディスコース分析を使用
        
        # 接続語の存在（高い方が一貫性がある）
        connectives = [
            "therefore", "however", "thus", "furthermore", "moreover", "in addition",
            "consequently", "meanwhile", "nevertheless", "although", "despite",
            "したがって", "しかし", "さらに", "加えて", "その結果", "一方", "それにもかかわらず", "にもかかわらず"
        ]
        
        sentences = re.split(r'[.!?。！？]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return 0.7  # 文が1つの場合のデフォルト値
        
        # 接続語の数をカウント
        connective_count = sum(response.lower().count(conn) for conn in connectives)
        connective_score = min(connective_count / (len(sentences) - 1), 0.5)  # 最大0.5のボーナス
        
        # 代名詞の一貫した使用
        pronouns = ["it", "they", "this", "these", "those", "he", "she", "we", "それ", "彼", "彼女", "我々", "これ", "これら"]
        pronoun_count = sum(response.lower().count(" " + p + " ") for p in pronouns)
        
        # 代名詞が多すぎると明確さが低下する可能性
        optimal_pronoun_ratio = 0.05  # 全単語の5%が適切と仮定
        actual_pronoun_ratio = pronoun_count / max(len(self._tokenize(response)), 1)
        pronoun_score = 1.0 - min(abs(actual_pronoun_ratio - optimal_pronoun_ratio) * 10, 0.3)  # 最大0.3のペナルティ
        
        coherence_score = 0.5 + connective_score + (pronoun_score - 0.7)  # ベース0.5から調整
        return min(max(coherence_score, 0.0), 1.0)  # 0〜1の範囲に制限
    
    def _tokenize(self, text: str) -> List[str]:
        """
        テキストをトークン（単語）に分割
        """
        # これは簡略化された実装
        # 単純な空白と句読点による分割
        return re.findall(r'\w+', text)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        テキストからキーフレーズを抽出
        """
        # これは簡略化された実装
        # 名詞句や重要な表現を抽出
        
        # 2-3単語の連続を抽出（簡易的なフレーズ抽出）
        words = self._tokenize(text)
        phrases = []
        
        if len(words) >= 2:
            phrases.extend([" ".join(words[i:i+2]) for i in range(len(words)-1)])
        
        if len(words) >= 3:
            phrases.extend([" ".join(words[i:i+3]) for i in range(len(words)-2)])
        
        return phrases
    
    def _calculate_priority(self, current_score: float, threshold: float) -> int:
        """
        現在のスコアと閾値に基づいて優先度を計算
        """
        if current_score < threshold * 0.7:
            return 5  # 最高優先度
        elif current_score < threshold * 0.8:
            return 4
        elif current_score < threshold * 0.9:
            return 3
        elif current_score < threshold:
            return 2
        else:
            return 1  # 最低優先度
