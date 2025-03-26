"""
思考エンジン

問題解決、論理的推論、決定を行うための思考プロセスを実装。
LLMが利用可能な場合はそれを使用し、なければルールベースの思考を提供。
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

class ThinkingEngine:
    """
    AIシステムの思考プロセスを管理するクラス
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        ThinkingEngineの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        self.logger = logging.getLogger("thinking_engine")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                self.config = config.get("thinking", {})
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {}
        
        # 思考履歴
        self.thinking_history = []
        
        # 思考モードの定義
        self.thinking_modes = {
            "quick": "簡単な応答や明確な質問に対する迅速な思考",
            "analytical": "複雑な問題を論理的に分析する思考",
            "creative": "新しいアイデアや解決策を生み出す創造的思考",
            "critical": "仮説や提案を評価し検証する批判的思考",
            "strategic": "長期的な目標や計画に関する戦略的思考",
            "reflective": "自己の思考や行動を振り返る内省的思考"
        }
        
        # 思考プロセスのテンプレート
        self.thinking_templates = {
            "analytical": [
                "問題の定義: {problem}",
                "関連する既知の情報: {known_info}",
                "情報ギャップ: {info_gaps}",
                "仮説: {hypothesis}",
                "分析: {analysis}",
                "結論: {conclusion}"
            ],
            "creative": [
                "課題: {challenge}",
                "既存のアプローチ: {existing_approaches}",
                "新しい視点: {new_perspectives}",
                "アイデア生成: {ideas}",
                "アイデア評価: {evaluation}",
                "提案: {proposal}"
            ],
            "critical": [
                "評価対象: {subject}",
                "主な主張: {claims}",
                "前提条件: {assumptions}",
                "証拠の評価: {evidence_evaluation}",
                "論理的一貫性: {logical_consistency}",
                "批判的見解: {critical_view}"
            ],
            "strategic": [
                "目標: {goal}",
                "現状分析: {current_state}",
                "機会と脅威: {opportunities_threats}",
                "可能な戦略: {possible_strategies}",
                "リソースと制約: {resources_constraints}",
                "推奨戦略: {recommended_strategy}"
            ],
            "reflective": [
                "振り返り対象: {reflection_subject}",
                "行動の振り返り: {action_review}",
                "結果の分析: {result_analysis}",
                "学び: {lessons_learned}",
                "改善点: {improvements}",
                "次のステップ: {next_steps}"
            ]
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
        
        self.logger.info("Thinking engine initialized")
    
    def think(self, query: str, context: Dict[str, Any] = None, 
            mode: str = "analytical", depth: int = 1) -> Dict[str, Any]:
        """
        指定されたクエリとコンテキストに対して思考プロセスを実行
        
        Args:
            query: 思考の対象となるクエリ
            context: 関連するコンテキスト情報
            mode: 思考モード
            depth: 思考の深さ（1-3）
            
        Returns:
            思考プロセスと結果
        """
        start_time = time.time()
        
        # 思考モードの検証
        if mode not in self.thinking_modes:
            self.logger.warning(f"Invalid thinking mode: {mode}, using analytical")
            mode = "analytical"
        
        # 思考の深さを1-3に制限
        depth = max(1, min(3, depth))
        
        self.logger.info(f"Thinking about: {query} (mode: {mode}, depth: {depth})")
        
        # 思考履歴の長さを制限
        if len(self.thinking_history) > 100:
            self.thinking_history = self.thinking_history[-100:]
        
        # 1. LLMが利用可能ならLLMベースの思考
        if self.llm:
            thinking_result = self._think_with_llm(query, context, mode, depth)
        else:
            # 2. LLMが利用できない場合はルールベースの思考
            thinking_result = self._think_with_rules(query, context, mode, depth)
        
        # 実行時間を追加
        duration = time.time() - start_time
        thinking_result["duration_seconds"] = duration
        
        # 思考履歴に追加
        thinking_entry = {
            "query": query,
            "mode": mode,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "conclusion": thinking_result.get("conclusion", "")
        }
        self.thinking_history.append(thinking_entry)
        
        self.logger.info(f"Thinking completed in {duration:.2f} seconds")
        return thinking_result
    
    def reflect(self, action: str, result: str, 
              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        特定の行動とその結果について振り返る
        
        Args:
            action: 振り返る行動の説明
            result: 行動の結果
            context: 関連するコンテキスト情報
            
        Returns:
            振り返りの結果
        """
        # reflectiveモードの思考プロセスを使用
        return self.think(
            query=f"行動「{action}」とその結果「{result}」の振り返り",
            context=context,
            mode="reflective",
            depth=2
        )
    
    def decide(self, options: List[Dict[str, Any]], 
             criteria: List[Dict[str, Any]] = None,
             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        複数の選択肢から意思決定を行う
        
        Args:
            options: 選択肢のリスト（各選択肢はid, description, value等を含む辞書）
            criteria: 判断基準のリスト（各基準はname, weightを含む辞書）
            context: 関連するコンテキスト情報
            
        Returns:
            決定プロセスと結果
        """
        if not options:
            return {
                "status": "error",
                "message": "No options provided for decision",
                "decision": None
            }
        
        # 選択肢の数が1つだけの場合は自明
        if len(options) == 1:
            return {
                "status": "success",
                "message": "Only one option available",
                "decision": options[0],
                "process": "Single option selected automatically"
            }
        
        # 判断基準がない場合はデフォルト基準を設定
        if not criteria:
            criteria = [
                {"name": "効率性", "weight": 1.0},
                {"name": "信頼性", "weight": 1.0},
                {"name": "実現可能性", "weight": 1.0}
            ]
        
        # analytical モードの思考で意思決定
        query = f"選択肢から最適な選択を行う: {', '.join(opt.get('description', '') for opt in options)}"
        
        # コンテキストに選択肢と基準を追加
        decision_context = context or {}
        decision_context["options"] = options
        decision_context["criteria"] = criteria
        
        # 思考プロセスを実行
        thinking_result = self.think(
            query=query,
            context=decision_context,
            mode="analytical",
            depth=2
        )
        
        # 選択肢評価（スコア付け）
        option_scores = {}
        for option in options:
            option_id = option.get("id", str(id(option)))
            score = 0.0
            
            # 1. LLMが利用可能な場合は結論から最適選択肢を抽出
            if "conclusion" in thinking_result and self.llm:
                conclusion = thinking_result["conclusion"]
                if option.get("description", "") in conclusion:
                    # 結論に選択肢の説明が含まれている場合、スコアを上げる
                    score += 2.0
            
            # 2. ルールベースのスコアリング
            for criterion in criteria:
                criterion_name = criterion.get("name", "")
                criterion_weight = criterion.get("weight", 1.0)
                
                # 選択肢が基準に合致する特性を持っているか評価
                if criterion_name in option.get("description", "").lower():
                    score += criterion_weight
                
                # 選択肢の属性に基づく評価
                if "attributes" in option:
                    for attr_name, attr_value in option["attributes"].items():
                        if criterion_name in attr_name.lower():
                            # 数値属性の場合
                            if isinstance(attr_value, (int, float)):
                                # 値が大きいほど良い属性と仮定
                                score += attr_value * criterion_weight * 0.1
                            # ブール属性の場合
                            elif isinstance(attr_value, bool) and attr_value:
                                score += criterion_weight
            
            option_scores[option_id] = score
        
        # 最高スコアの選択肢を選定
        best_option_id = max(option_scores, key=option_scores.get)
        best_option = next((opt for opt in options if opt.get("id", str(id(opt))) == best_option_id), options[0])
        
        return {
            "status": "success",
            "decision": best_option,
            "scores": option_scores,
            "process": thinking_result,
            "message": f"決定: {best_option.get('description', '')}"
        }
    
    def analyze_problem(self, problem_description: str, 
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        問題分析を実行
        
        Args:
            problem_description: 問題の説明
            context: 関連するコンテキスト情報
            
        Returns:
            問題分析の結果
        """
        # analytical モードで問題分析を実行
        return self.think(
            query=f"問題分析: {problem_description}",
            context=context,
            mode="analytical",
            depth=3  # 最大の深さで詳細に分析
        )
    
    def generate_ideas(self, challenge: str, 
                      context: Dict[str, Any] = None,
                      count: int = 3) -> Dict[str, Any]:
        """
        創造的なアイデア生成
        
        Args:
            challenge: 課題や挑戦の説明
            context: 関連するコンテキスト情報
            count: 生成するアイデアの数
            
        Returns:
            アイデア生成の結果
        """
        # アイデア数を制限
        count = max(1, min(10, count))
        
        # creative モードで思考プロセスを実行
        thinking_result = self.think(
            query=f"課題「{challenge}」に対する{count}個のアイデア生成",
            context=context,
            mode="creative",
            depth=2
        )
        
        # アイデアを抽出
        ideas = []
        
        # 1. LLMが利用可能な場合
        if "ideas" in thinking_result and self.llm:
            ideas_text = thinking_result["ideas"]
            
            # 箇条書きやナンバリングされたアイデアを抽出
            idea_patterns = [
                r'[\-\*]\s*(.*?)(?=[\-\*]|$)',  # 箇条書き
                r'\d+\.\s*(.*?)(?=\d+\.|$)',    # 番号付きリスト
                r'「(.*?)」',                    # 括弧で囲まれたアイデア
                r'"([^"]*)"'                    # ダブルクォートで囲まれたアイデア
            ]
            
            extracted_ideas = []
            for pattern in idea_patterns:
                found = re.findall(pattern, ideas_text, re.DOTALL)
                if found:
                    extracted_ideas.extend([idea.strip() for idea in found if idea.strip()])
            
            # 重複を除去
            unique_ideas = []
            for idea in extracted_ideas:
                if idea not in unique_ideas:
                    unique_ideas.append(idea)
            
            # 構造化
            for i, idea_text in enumerate(unique_ideas[:count]):
                ideas.append({
                    "id": f"idea_{i+1}",
                    "description": idea_text,
                    "source": "creative_thinking"
                })
        
        # 2. ルールベースのアイデア生成（LLMがない場合や結果が不十分な場合）
        if len(ideas) < count:
            # 簡易的なアイデア生成
            keywords = self._extract_keywords(challenge)
            
            base_ideas = [
                "既存の解決策を別の文脈に適用する",
                "問題を逆の視点から考える",
                "複数の既存のアプローチを組み合わせる",
                "制約の一部を取り除いて考える",
                "自然の仕組みから着想を得る",
                "まったく異なる分野の解決法を応用する",
                "最小限の機能から始めて段階的に拡張する",
                "ユーザーの視点に立って再定義する",
                "試行錯誤と反復的なプロトタイピング",
                "専門家と非専門家の視点を組み合わせる"
            ]
            
            for i in range(len(ideas), count):
                if i < len(base_ideas):
                    # キーワードを含めたアイデア生成
                    if keywords:
                        keyword = keywords[i % len(keywords)]
                        idea_text = f"{base_ideas[i]}：{keyword}を活用した新しいアプローチ"
                    else:
                        idea_text = base_ideas[i]
                    
                    ideas.append({
                        "id": f"idea_{i+1}",
                        "description": idea_text,
                        "source": "rule_based"
                    })
        
        # アイデア生成結果を構造化
        result = {
            "challenge": challenge,
            "ideas_count": len(ideas),
            "ideas": ideas,
            "thinking_process": thinking_result
        }
        
        return result
    
    def get_thinking_stats(self) -> Dict[str, Any]:
        """
        思考エンジンの統計情報を取得
        
        Returns:
            統計情報
        """
        if not self.thinking_history:
            return {
                "total_thinking_sessions": 0,
                "avg_duration_seconds": 0,
                "mode_distribution": {},
                "llm_available": self.llm is not None
            }
        
        # 思考モードの分布
        mode_counts = {}
        for entry in self.thinking_history:
            mode = entry.get("mode", "unknown")
            if mode not in mode_counts:
                mode_counts[mode] = 1
            else:
                mode_counts[mode] += 1
        
        # 平均処理時間
        avg_duration = sum(entry.get("duration_seconds", 0) for entry in self.thinking_history) / len(self.thinking_history)
        
        # 深さの分布
        depth_counts = {}
        for entry in self.thinking_history:
            depth = entry.get("depth", 0)
            if depth not in depth_counts:
                depth_counts[depth] = 1
            else:
                depth_counts[depth] += 1
        
        return {
            "total_thinking_sessions": len(self.thinking_history),
            "avg_duration_seconds": avg_duration,
            "mode_distribution": mode_counts,
            "depth_distribution": depth_counts,
            "llm_available": self.llm is not None,
            "last_thinking": self.thinking_history[-1] if self.thinking_history else None
        }
    
    def _think_with_llm(self, query: str, context: Dict[str, Any], mode: str, depth: int) -> Dict[str, Any]:
        """LLMを使用して思考プロセス実行"""
        if not self.llm:
            return self._think_with_rules(query, context, mode, depth)
        
        # コンテキスト情報の整形
        context_str = ""
        if context:
            context_items = []
            for key, value in context.items():
                if isinstance(value, (list, dict)):
                    # 複雑な構造はJSON形式に変換
                    context_items.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
                else:
                    context_items.append(f"{key}: {value}")
            
            if context_items:
                context_str = "コンテキスト情報:\n" + "\n".join(context_items)
        
        # 思考の深さに応じてプロンプト調整
        depth_instructions = {
            1: "基本的な分析を行い、簡潔な回答を提供してください。",
            2: "詳細な分析を行い、複数の視点から考察してください。",
            3: "徹底的な分析を行い、あらゆる側面を考慮した深い考察を提供してください。"
        }
        
        # 思考モードに対応するテンプレートを取得
        template = self.thinking_templates.get(mode, [])
        
        # プロンプトの作成
        prompt = f"""
        以下のクエリについて、{self.thinking_modes.get(mode, '論理的')}思考で分析してください。
        
        クエリ: {query}
        
        {context_str}
        
        {depth_instructions.get(depth, "")}
        
        以下のステップで思考を進めてください:
        """
        
        # テンプレートがある場合は使用
        if template:
            for step in template:
                prompt += f"\n{step}"
        else:
            # 汎用的な思考ステップ
            prompt += """
            1. 問題の定義
            2. 関連する情報の分析
            3. 可能性の検討
            4. 論理的推論
            5. 結論または回答
            """
        
        prompt += """
        
        各ステップを明示的に示し、最終的な結論を提供してください。
        JSON形式で回答する必要はありません。自然な思考の流れで回答してください。
        """
        
        try:
            # LLMに思考プロセスを生成させる
            result = self.llm(prompt, max_tokens=4096, temperature=0.7)
            
            # 結果の解析と構造化
            thinking_result = self._parse_thinking_result(result, mode)
            
            # メタデータを追加
            thinking_result["query"] = query
            thinking_result["mode"] = mode
            thinking_result["depth"] = depth
            thinking_result["method"] = "llm"
            
            return thinking_result
            
        except Exception as e:
            self.logger.error(f"Error using LLM for thinking: {str(e)}")
            # フォールバックとしてルールベース思考を使用
            return self._think_with_rules(query, context, mode, depth)
    
    def _think_with_rules(self, query: str, context: Dict[str, Any], mode: str, depth: int) -> Dict[str, Any]:
        """ルールベースの思考プロセス実行"""
        thinking_result = {
            "query": query,
            "mode": mode,
            "depth": depth,
            "method": "rule_based"
        }
        
        # 思考モードに基づく処理
        if mode == "analytical":
            # 分析的思考
            thinking_result["problem"] = f"分析対象: {query}"
            
            # 既知情報の抽出
            known_info = []
            if context:
                for key, value in context.items():
                    if isinstance(value, (str, int, float, bool)):
                        known_info.append(f"{key}: {value}")
                    elif isinstance(value, (list, dict)):
                        known_info.append(f"{key}: 複合データ")
            
            thinking_result["known_info"] = "特に既知情報なし" if not known_info else "\n".join(known_info)
            
            # 情報ギャップの特定
            info_gaps = ["詳細な例が不足しています", "時間的文脈が明確でありません", "対象の制約条件が不明確です"]
            thinking_result["info_gaps"] = "\n".join(info_gaps)
            
            # 仮説
            keywords = self._extract_keywords(query)
            hypothesis = f"「{query}」は"
            if keywords:
                hypothesis += f"「{keywords[0]}」と「{keywords[-1] if len(keywords) > 1 else '関連要素'}」の関係性に関わる問題と考えられます。"
            else:
                hypothesis += "複数の要素が絡む複合的な問題と考えられます。"
            
            thinking_result["hypothesis"] = hypothesis
            
            # 分析
            thinking_result["analysis"] = f"この問題を分析するには、まず{query}の主要構成要素を特定し、それらの関係性を明らかにすることが重要です。"
            
            # 結論
            thinking_result["conclusion"] = f"{query}については、入力された情報からは限定的な分析しかできません。より詳細な情報があれば、より正確な分析が可能です。"
            
        elif mode == "creative":
            # 創造的思考
            thinking_result["challenge"] = f"創造的課題: {query}"
            
            # 既存アプローチ
            thinking_result["existing_approaches"] = "既存の一般的なアプローチとしては、従来の方法論や標準的な解決策が考えられます。"
            
            # 新しい視点
            thinking_result["new_perspectives"] = f"この課題を別の角度から見ると、{query}を全く異なる文脈で捉え直すことができます。"
            
            # アイデア生成
            keywords = self._extract_keywords(query)
            ideas = []
            
            base_ideas = [
                "既存の解決策を別の文脈に適用する",
                "問題を逆の視点から考える",
                "複数の既存のアプローチを組み合わせる",
                "制約の一部を取り除いて考える",
                "自然の仕組みから着想を得る"
            ]
            
            for i, base in enumerate(base_ideas[:3]):  # 最大3つのアイデア
                if i < len(keywords):
                    ideas.append(f"{base}：{keywords[i]}を活用した新しいアプローチ")
                else:
                    ideas.append(base)
            
            thinking_result["ideas"] = "\n".join(ideas)
            
            # アイデア評価
            thinking_result["evaluation"] = "これらのアイデアは一般的なものです。実際の適用には具体的な文脈と詳細な検討が必要です。"
            
            # 提案
            thinking_result["proposal"] = f"{query}に対する最も有望なアプローチは、状況に応じて複数のアイデアを組み合わせることかもしれません。"
            
        elif mode == "critical":
            # 批判的思考
            thinking_result["subject"] = f"評価対象: {query}"
            
            # 主張の抽出
            thinking_result["claims"] = f"{query}には、特定の前提や主張が含まれている可能性があります。それらを具体的に特定するには追加情報が必要です。"
            
            # 前提条件
            thinking_result["assumptions"] = "一般的な前提として、問題が明確に定義されており、標準的な解決法が適用可能であることが考えられます。"
            
            # 証拠評価
            thinking_result["evidence_evaluation"] = "現時点では、評価に必要な具体的な証拠や情報が不足しています。"
            
            # 論理的一貫性
            thinking_result["logical_consistency"] = "論理的一貫性の評価には、より詳細な情報構造の分析が必要です。"
            
            # 批判的見解
            thinking_result["critical_view"] = f"{query}については、より多角的な視点からの検証と追加情報が必要です。"
            
        else:
            # デフォルトの汎用的な思考プロセス
            thinking_result["initial_thoughts"] = f"{query}について考察します。"
            thinking_result["analysis"] = "限られた情報から可能な範囲で分析を行います。"
            thinking_result["conclusion"] = f"現在の情報では、{query}について確定的な結論を出すことは難しいです。より詳細な情報が必要です。"
        
        return thinking_result
    
    def _parse_thinking_result(self, thinking_text: str, mode: str) -> Dict[str, Any]:
        """LLMからの思考テキストを解析して構造化"""
        result = {}
        
        # 思考モードに応じたセクション抽出
        if mode in self.thinking_templates:
            template = self.thinking_templates[mode]
            
            for step in template:
                # セクション名を抽出（例: "問題の定義: {problem}" から "問題の定義"）
                section_match = re.match(r'([^:]+):', step)
                if section_match:
                    section_name = section_match.group(1).strip()
                    # テンプレート変数名を抽出（例: "{problem}" から "problem"）
                    var_match = re.search(r'{([^}]+)}', step)
                    if var_match:
                        var_name = var_match.group(1)
                        
                        # テキストからそのセクションを探す
                        pattern = fr'{re.escape(section_name)}:\s*(.*?)(?=\n\s*(?:{"|".join(re.escape(s.split(":")[0]) for s in template if ":" in s)})|$)'
                        section_match = re.search(pattern, thinking_text, re.DOTALL | re.IGNORECASE)
                        
                        if section_match:
                            section_content = section_match.group(1).strip()
                            result[var_name] = section_content
        
        # 結論のチェック（特に重要）
        if "conclusion" not in result:
            conclusion_patterns = [
                r'結論(?::|：)\s*(.*?)(?=\n\s*(?:$))',
                r'まとめ(?::|：)\s*(.*?)(?=\n\s*(?:$))',
                r'総括(?::|：)\s*(.*?)(?=\n\s*(?:$))',
                r'最終的な判断(?::|：)\s*(.*?)(?=\n\s*(?:$))'
            ]
            
            for pattern in conclusion_patterns:
                match = re.search(pattern, thinking_text, re.DOTALL)
                if match:
                    result["conclusion"] = match.group(1).strip()
                    break
        
        # 全体のテキストも保存
        result["full_thinking"] = thinking_text.strip()
        
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        # 簡易的なキーワード抽出（日本語と英語に対応）
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
