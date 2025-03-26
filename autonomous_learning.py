"""
自律学習モジュール

知識ギャップの特定、学習計画の作成、知識の自動獲得を行うシステム。
自己成長AIの中核となる知識学習コンポーネント。
"""

import logging
import json
import time
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# ローカルLLMを利用するためのインポート（実際の環境に合わせて変更）
try:
    from llama_cpp import Llama
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# バックアップとしてのルールベース処理
from knowledge_base import KnowledgeBase
from web_searcher import WebSearcher

class AutonomousLearning:
    """
    自律的な学習プロセスを管理するクラス
    知識ギャップの特定、学習計画の作成、知識の獲得を自律的に行う
    """
    
    def __init__(self, kb: KnowledgeBase, web_searcher: WebSearcher, config_path: str = "config.json"):
        """
        AutonomousLearningの初期化
        
        Args:
            kb: 知識ベースインスタンス
            web_searcher: Web検索インスタンス
            config_path: 設定ファイルへのパス
        """
        self.kb = kb
        self.web_searcher = web_searcher
        self.logger = logging.getLogger("autonomous_learning")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                self.config = config.get("autonomous_learning", {})
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {}
        
        # 学習履歴
        self.learning_history = []
        
        # 現在の学習計画
        self.active_learning_plans = {}
        
        # 知識ドメイン定義
        self.knowledge_domains = {
            "science": ["physics", "chemistry", "biology", "astronomy", "geology"],
            "technology": ["programming", "artificial intelligence", "machine learning", "software", "hardware", "internet"],
            "mathematics": ["algebra", "calculus", "geometry", "statistics", "probability"],
            "history": ["ancient history", "medieval history", "modern history", "world wars", "civilizations"],
            "arts": ["literature", "music", "painting", "sculpture", "architecture", "cinema"],
            "philosophy": ["ethics", "logic", "metaphysics", "epistemology", "aesthetics"],
            "social_sciences": ["psychology", "sociology", "anthropology", "economics", "political science"]
        }
        
        # ローカルLLMの初期化（利用可能な場合）
        self.llm = None
        if LLM_AVAILABLE and self.config.get("use_local_llm", False):
            model_path = self.config.get("llm_model_path", "models/llama-2-7b-chat.Q4_K_M.gguf")
            if os.path.exists(model_path):
                try:
                    self.llm = Llama(
                        model_path=model_path,
                        n_ctx=self.config.get("llm_context_length", 2048),
                        n_threads=self.config.get("llm_threads", 4)
                    )
                    self.logger.info(f"Local LLM initialized: {model_path}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize LLM: {str(e)}")
        
        self.logger.info("Autonomous learning system initialized")
    
    def identify_knowledge_gaps(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        知識ギャップを特定
        
        Args:
            query: ユーザークエリ
            context: 会話コンテキスト（省略可）
            
        Returns:
            特定された知識ギャップのリスト
        """
        self.logger.info(f"Identifying knowledge gaps for: {query}")
        
        gaps = []
        
        # 1. LLMが利用可能ならLLMベースの分析
        if self.llm:
            gaps = self._identify_gaps_with_llm(query, context)
        
        # 2. LLMが利用できないか、結果が不十分な場合はルールベースの分析
        if not gaps:
            gaps = self._identify_gaps_with_rules(query, context)
        
        # 重複の除去と優先順位付け
        unique_gaps = []
        seen_topics = set()
        
        for gap in gaps:
            topic = gap.get("topic", "").lower()
            if topic and topic not in seen_topics:
                seen_topics.add(topic)
                
                # 知識ベースを検索して知識の有無を確認
                kb_results = self.kb.search_knowledge(topic, limit=3)
                if kb_results["total_results"] == 0:
                    # 知識ベースに情報がない場合は優先度を上げる
                    gap["priority"] = min(gap.get("priority", 3) + 1, 5)
                
                unique_gaps.append(gap)
        
        # 優先度でソート
        sorted_gaps = sorted(unique_gaps, key=lambda x: x.get("priority", 0), reverse=True)
        
        self.logger.info(f"Identified {len(sorted_gaps)} knowledge gaps")
        return sorted_gaps
    
    def create_learning_plan(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """
        知識ギャップに対する学習計画を作成
        
        Args:
            gap: 知識ギャップ情報
            
        Returns:
            学習計画
        """
        topic = gap.get("topic", "")
        if not topic:
            self.logger.warning("Cannot create learning plan: no topic specified")
            return {"status": "error", "message": "No topic specified"}
        
        self.logger.info(f"Creating learning plan for topic: {topic}")
        
        # 既存の学習計画をチェック
        for plan_id, plan in self.active_learning_plans.items():
            if plan.get("topic") == topic:
                self.logger.info(f"Learning plan already exists for topic: {topic}")
                return plan
        
        # 1. LLMが利用可能ならLLMベースの計画作成
        if self.llm:
            plan = self._create_plan_with_llm(gap)
        else:
            # 2. ルールベースの計画作成
            plan = self._create_plan_with_rules(gap)
        
        # 計画IDの生成
        plan_id = f"plan_{int(time.time())}_{len(self.active_learning_plans)}"
        plan["id"] = plan_id
        plan["status"] = "active"
        plan["created_at"] = datetime.now().isoformat()
        plan["progress"] = 0
        
        # アクティブな学習計画に追加
        self.active_learning_plans[plan_id] = plan
        
        # 学習履歴に記録
        self.learning_history.append({
            "event": "plan_created",
            "plan_id": plan_id,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
        
        return plan
    
    def execute_learning_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        学習計画を実行
        
        Args:
            plan_id: 学習計画ID
            
        Returns:
            実行結果
        """
        if plan_id not in self.active_learning_plans:
            self.logger.warning(f"Learning plan not found: {plan_id}")
            return {"status": "error", "message": "Learning plan not found"}
        
        plan = self.active_learning_plans[plan_id]
        topic = plan.get("topic", "")
        
        self.logger.info(f"Executing learning plan: {plan_id} for topic: {topic}")
        
        results = {
            "plan_id": plan_id,
            "topic": topic,
            "steps_completed": 0,
            "knowledge_acquired": 0,
            "status": "in_progress",
            "steps_results": {}
        }
        
        # 各ステップを実行
        for i, step in enumerate(plan.get("steps", [])):
            step_id = step.get("id", f"step_{i}")
            description = step.get("description", "")
            
            # 検索クエリの生成
            search_query = self._generate_search_query(topic, step)
            
            # Web検索の実行
            search_results = self.web_searcher.search(search_query, max_results=5)
            
            # 知識の抽出と保存
            acquired_knowledge = []
            if search_results.get("status") in ["success", "partial_success"]:
                for result in search_results.get("results", []):
                    # 詳細なコンテンツを取得（必要な場合）
                    if result.get("url") and len(result.get("content", "")) < 200:
                        detailed_content = self.web_searcher.get_article_content(result["url"])
                        if detailed_content.get("status") == "success":
                            result["detailed_content"] = detailed_content.get("content", "")
                    
                    # 知識の抽出
                    knowledge_items = self._extract_knowledge(result, topic)
                    
                    # 知識ベースに保存
                    for item in knowledge_items:
                        if item.get("type") == "fact":
                            fact_id = self.kb.store_fact(
                                content=item.get("content", ""),
                                source=result.get("url", ""),
                                confidence=item.get("confidence", 0.7),
                                category=item.get("category", "general")
                            )
                            if fact_id > 0:
                                item["id"] = fact_id
                                acquired_knowledge.append(item)
                        
                        elif item.get("type") == "concept":
                            concept_id = self.kb.store_concept(
                                name=item.get("name", ""),
                                description=item.get("content", ""),
                                definitions=[{"content": item.get("content", "")}],
                                confidence=item.get("confidence", 0.7)
                            )
                            if concept_id > 0:
                                item["id"] = concept_id
                                acquired_knowledge.append(item)
                        
                        elif item.get("type") == "relation":
                            if item.get("source_concept") and item.get("target_concept"):
                                relation_id = self.kb.store_relation(
                                    source_concept=item.get("source_concept", ""),
                                    target_concept=item.get("target_concept", ""),
                                    relation_type=item.get("relation_type", "related_to"),
                                    description=item.get("content", ""),
                                    confidence=item.get("confidence", 0.7)
                                )
                                if relation_id > 0:
                                    item["id"] = relation_id
                                    acquired_knowledge.append(item)
            
            # ステップ結果の記録
            step_result = {
                "step_id": step_id,
                "description": description,
                "search_query": search_query,
                "search_results_count": len(search_results.get("results", [])),
                "knowledge_acquired": len(acquired_knowledge),
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }
            
            results["steps_results"][step_id] = step_result
            results["steps_completed"] += 1
            results["knowledge_acquired"] += len(acquired_knowledge)
            
            # 進捗の更新
            progress = (results["steps_completed"] / len(plan.get("steps", []))) * 100
            plan["progress"] = progress
            
            # 学習履歴に記録
            self.learning_history.append({
                "event": "step_completed",
                "plan_id": plan_id,
                "step_id": step_id,
                "topic": topic,
                "knowledge_acquired": len(acquired_knowledge),
                "timestamp": datetime.now().isoformat()
            })
        
        # 学習計画の完了
        if results["steps_completed"] == len(plan.get("steps", [])):
            plan["status"] = "completed"
            plan["completed_at"] = datetime.now().isoformat()
            results["status"] = "completed"
            
            # 学習履歴に記録
            self.learning_history.append({
                "event": "plan_completed",
                "plan_id": plan_id,
                "topic": topic,
                "total_knowledge_acquired": results["knowledge_acquired"],
                "timestamp": datetime.now().isoformat()
            })
        
        return results
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        学習統計を取得
        
        Returns:
            学習統計情報
        """
        total_plans = len(self.learning_history)
        completed_plans = sum(1 for event in self.learning_history if event.get("event") == "plan_completed")
        
        # トピック別の学習数
        topic_counts = {}
        for event in self.learning_history:
            if event.get("topic"):
                topic = event.get("topic")
                if topic not in topic_counts:
                    topic_counts[topic] = 1
                else:
                    topic_counts[topic] += 1
        
        # 総獲得知識数
        total_knowledge_acquired = sum(
            event.get("total_knowledge_acquired", 0) 
            for event in self.learning_history 
            if event.get("event") == "plan_completed"
        )
        
        # アクティブな学習計画
        active_plans = len([p for p in self.active_learning_plans.values() if p.get("status") == "active"])
        
        return {
            "total_learning_plans": total_plans,
            "completed_plans": completed_plans,
            "active_plans": active_plans,
            "total_knowledge_acquired": total_knowledge_acquired,
            "topics_learned": len(topic_counts),
            "topic_distribution": topic_counts,
            "last_learning_event": self.learning_history[-1] if self.learning_history else None
        }
    
    def _identify_gaps_with_llm(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """LLMを使用して知識ギャップを特定"""
        if not self.llm:
            return []
        
        prompt = f"""
        ユーザーの質問やコンテキストを分析し、AIシステムが持つべき知識のギャップを特定してください。
        質問: {query}
        
        知識ギャップを特定するには以下を考慮してください:
        1. 質問に含まれる主要な概念や専門用語
        2. 質問に答えるために必要な背景知識
        3. 関連する上位概念と派生概念
        
        以下の形式で知識ギャップを3-5個リストアップしてください:
        
        [
          {{
            "topic": "ギャップのトピック",
            "description": "このトピックについて学ぶ必要がある理由",
            "priority": ギャップの優先度(1-5、5が最高),
            "domain": "該当する知識ドメイン",
            "related_to": "元の質問との関連性"
          }}
        ]
        
        JSONのみを出力してください。
        """
        
        try:
            result = self.llm(prompt, max_tokens=2048, temperature=0.2)
            # JSONの抽出
            json_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                gaps = json.loads(json_str)
                return gaps
        except Exception as e:
            self.logger.error(f"Error using LLM for gap identification: {str(e)}")
        
        return []
    
    def _identify_gaps_with_rules(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """ルールベースの方法で知識ギャップを特定"""
        gaps = []
        
        # 簡単なキーワード抽出
        keywords = self._extract_keywords(query)
        
        # 各キーワードについて知識ベースを検索
        for keyword in keywords:
            kb_results = self.kb.search_knowledge(keyword, limit=1)
            
            # 知識ベースに情報がない場合はギャップとして登録
            if kb_results["total_results"] == 0:
                # キーワードのドメイン推定
                domain = self._estimate_domain(keyword)
                
                gap = {
                    "topic": keyword,
                    "description": f"「{keyword}」に関する基本情報が必要",
                    "priority": 3,  # デフォルト優先度
                    "domain": domain,
                    "related_to": query
                }
                
                gaps.append(gap)
        
        # query 全体で直接検索
        if not gaps:
            kb_results = self.kb.search_knowledge(query, limit=1)
            if kb_results["total_results"] == 0:
                domain = self._estimate_domain(query)
                
                gap = {
                    "topic": query,
                    "description": f"質問全体に関する情報が必要",
                    "priority": 4,  # クエリ全体はやや優先
                    "domain": domain,
                    "related_to": query
                }
                
                gaps.append(gap)
        
        return gaps
    
    def _create_plan_with_llm(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """LLMを使用して学習計画を作成"""
        if not self.llm:
            return self._create_plan_with_rules(gap)
        
        topic = gap.get("topic", "")
        description = gap.get("description", "")
        domain = gap.get("domain", "general")
        
        prompt = f"""
        以下の知識ギャップに対する学習計画を作成してください。
        
        トピック: {topic}
        説明: {description}
        ドメイン: {domain}
        
        学習計画には、このトピックを体系的に学ぶためのステップを含めてください。
        各ステップは検索クエリとそのステップの目的を含むべきです。
        
        以下の形式で回答してください:
        
        {{
          "topic": "{topic}",
          "domain": "{domain}",
          "objective": "この学習の全体的な目標",
          "steps": [
            {{
              "id": "step_1",
              "description": "ステップの説明",
              "search_query_suggestion": "Web検索に使用すべきクエリ",
              "expected_outcomes": "このステップで習得すべき知識"
            }}
          ]
        }}
        
        JSONのみを出力してください。
        """
        
        try:
            result = self.llm(prompt, max_tokens=2048, temperature=0.3)
            # JSONの抽出
            json_match = re.search(r'{.*}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                plan = json.loads(json_str)
                return plan
        except Exception as e:
            self.logger.error(f"Error using LLM for plan creation: {str(e)}")
        
        return self._create_plan_with_rules(gap)
    
    def _create_plan_with_rules(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """ルールベースの方法で学習計画を作成"""
        topic = gap.get("topic", "")
        domain = gap.get("domain", "general")
        
        # 基本的な学習ステップのテンプレート
        steps = [
            {
                "id": "step_1",
                "description": f"{topic}の基本概念と定義",
                "search_query_suggestion": f"{topic} 定義 基本概念",
                "expected_outcomes": "基本的な理解と定義の習得"
            },
            {
                "id": "step_2",
                "description": f"{topic}の主要な側面",
                "search_query_suggestion": f"{topic} 主要 特徴 側面",
                "expected_outcomes": "主要な特徴と側面の理解"
            },
            {
                "id": "step_3",
                "description": f"{topic}の実例または応用",
                "search_query_suggestion": f"{topic} 例 応用 実世界",
                "expected_outcomes": "実際の例や応用の習得"
            }
        ]
        
        # 特定ドメインに基づいた追加ステップ
        if domain == "science":
            steps.append({
                "id": "step_4",
                "description": f"{topic}に関する最新の研究や発見",
                "search_query_suggestion": f"{topic} 最新 研究 発見 進展",
                "expected_outcomes": "最新の科学的知見の習得"
            })
        elif domain == "technology":
            steps.append({
                "id": "step_4",
                "description": f"{topic}の技術動向と未来予測",
                "search_query_suggestion": f"{topic} 技術動向 未来 予測 最新",
                "expected_outcomes": "技術の進化と将来性についての理解"
            })
        elif domain == "history":
            steps.append({
                "id": "step_4",
                "description": f"{topic}の歴史的背景と影響",
                "search_query_suggestion": f"{topic} 歴史 背景 影響 重要性",
                "expected_outcomes": "歴史的文脈と重要性の理解"
            })
        
        # 関連概念の調査ステップ
        steps.append({
            "id": f"step_{len(steps) + 1}",
            "description": f"{topic}と関連する概念や分野",
            "search_query_suggestion": f"{topic} 関連 概念 分野 関係",
            "expected_outcomes": "関連する概念や分野との繋がりの理解"
        })
        
        return {
            "topic": topic,
            "domain": domain,
            "objective": f"{topic}に関する包括的な理解を得る",
            "steps": steps
        }
    
    def _generate_search_query(self, topic: str, step: Dict[str, Any]) -> str:
        """学習ステップに基づいて検索クエリを生成"""
        # ステップにサジェスションが含まれていればそれを使用
        if "search_query_suggestion" in step:
            return step["search_query_suggestion"]
        
        # ステップの説明に基づいてクエリを生成
        description = step.get("description", "")
        
        # 基本クエリ
        query = f"{topic} "
        
        # ステップの説明から追加のキーワードを抽出
        keywords = self._extract_keywords(description)
        if keywords:
            # 最大3つのキーワードを追加
            additional_keywords = " ".join(keywords[:3])
            query += additional_keywords
        
        return query
    
    def _extract_knowledge(self, search_result: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """検索結果から知識項目を抽出"""
        knowledge_items = []
        
        # コンテンツを取得
        content = search_result.get("detailed_content", search_result.get("content", ""))
        if not content:
            return []
        
        # セグメントに分割（段落や文ごと）
        segments = []
        
        # 段落分割
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            if p.strip():
                # 長い段落は文に分割
                if len(p) > 300:
                    sentences = re.split(r'(?<=[.!?])\s+', p)
                    segments.extend([s for s in sentences if len(s) > 20])
                else:
                    segments.append(p)
        
        # 各セグメントを分析
        for segment in segments:
            # 1. LLMが利用可能ならLLMベースの知識抽出
            if self.llm:
                items = self._extract_knowledge_with_llm(segment, topic)
                knowledge_items.extend(items)
                continue
            
            # 2. ルールベースの知識抽出
            item_type = self._determine_knowledge_type(segment)
            
            if item_type == "fact":
                knowledge_items.append({
                    "type": "fact",
                    "content": segment,
                    "confidence": 0.7,
                    "category": "general"
                })
            
            elif item_type == "concept":
                # トピックを概念名として扱う
                knowledge_items.append({
                    "type": "concept",
                    "name": topic,
                    "content": segment,
                    "confidence": 0.7
                })
            
            elif item_type == "relation":
                # 関係性を示すパターンを検出
                relation_match = re.search(r'(.+?)と(.+?)の関係', segment)
                if relation_match:
                    source = relation_match.group(1).strip()
                    target = relation_match.group(2).strip()
                    
                    knowledge_items.append({
                        "type": "relation",
                        "source_concept": source,
                        "target_concept": target,
                        "relation_type": "related_to",
                        "content": segment,
                        "confidence": 0.7
                    })
                else:
                    # トピックと別の概念の関係
                    # 簡易的なパターンマッチング
                    other_concept_match = re.search(r'(.+?)は|が(.+?)', segment)
                    if other_concept_match:
                        other_concept = other_concept_match.group(2).strip() if other_concept_match.group(2) else other_concept_match.group(1).strip()
                        
                        knowledge_items.append({
                            "type": "relation",
                            "source_concept": topic,
                            "target_concept": other_concept,
                            "relation_type": "related_to",
                            "content": segment,
                            "confidence": 0.7
                        })
        
        return knowledge_items
    
    def _extract_knowledge_with_llm(self, text: str, topic: str) -> List[Dict[str, Any]]:
        """LLMを使用してテキストから知識を抽出"""
        if not self.llm:
            return []
        
        prompt = f"""
        以下のテキストから「{topic}」に関する知識を抽出し、構造化してください。
        
        テキスト:
        "{text}"
        
        抽出された知識は以下のいずれかの形式で返してください:
        
        1. 事実 (fact):
        {{
          "type": "fact",
          "content": "抽出された事実",
          "confidence": 0.0～1.0の信頼度,
          "category": "カテゴリ（general, scientific, historical, etc.）"
        }}
        
        2. 概念 (concept):
        {{
          "type": "concept",
          "name": "概念名",
          "content": "概念の説明",
          "confidence": 0.0～1.0の信頼度
        }}
        
        3. 関係 (relation):
        {{
          "type": "relation",
          "source_concept": "起点の概念",
          "target_concept": "終点の概念",
          "relation_type": "関係タイプ (is_a, part_of, related_to)",
          "content": "関係の説明",
          "confidence": 0.0～1.0の信頼度
        }}
        
        複数の知識を抽出できる場合は、JSONの配列として返してください。
        テキストから意味のある知識が抽出できない場合は空の配列を返してください。
        JSONのみを出力してください。
        """
        
        try:
            result = self.llm(prompt, max_tokens=2048, temperature=0.2)
            # JSONの抽出
            json_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                items = json.loads(json_str)
                return items
            
            # 単一のJSONオブジェクト
            json_match = re.search(r'{.*}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                item = json.loads(json_str)
                return [item]
                
        except Exception as e:
            self.logger.error(f"Error using LLM for knowledge extraction: {str(e)}")
        
        return []
    
    def _determine_knowledge_type(self, text: str) -> str:
        """テキストの知識タイプを判定"""
        # 簡易的な判定ロジック
        text_lower = text.lower()
        
        # 定義パターン
        if re.search(r'は.+である|とは|definition|is defined as', text_lower):
            return "concept"
        
        # 関係パターン
        elif re.search(r'関係|関連|相関|依存|影響|between|relation|correlation', text_lower):
            return "relation"
        
        # それ以外は事実
        return "fact"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        # 簡易的なキーワード抽出
        # 停止語を除去し、頻出語を抽出
        
        words = []
        # 日本語と英語の単語を抽出
        ja_words = re.findall(r'[一-龠]+|[ぁ-ん]+|[ァ-ヴー]+', text)
        en_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        words = ja_words + en_words
        
        # 停止語の除去（日英）
        stopwords = {"the", "and", "is", "in", "to", "of", "for", "a", "with", "by", "on", "at",
                   "から", "より", "など", "または", "および", "それぞれ", "ただし", "および", "または",
                   "について", "による", "および", "または", "など", "という", "また", "その"}
        
        keywords = [w for w in words if w.lower() not in stopwords]
        
        return keywords
    
    def _estimate_domain(self, text: str) -> str:
        """テキストの知識ドメインを推定"""
        text_lower = text.lower()
        
        for domain, keywords in self.knowledge_domains.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return domain
        
        return "general"
