"""
知識ベース管理モジュール

知識の保存、取得、更新を管理するシステム。
sqlite3を使用して効率的で軽量なストレージを実現。
"""

import sqlite3
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re

class KnowledgeBase:
    """
    知識ベースを管理するクラス
    SQLiteを使用して効率的に知識を保存、検索、更新する
    """
    
    def __init__(self, db_path: str = "knowledge.db", config_path: str = "config.json"):
        """
        KnowledgeBaseの初期化
        
        Args:
            db_path: 知識ベースDBのパス
            config_path: 設定ファイルへのパス
        """
        self.db_path = db_path
        self.logger = logging.getLogger("knowledge_base")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {"default": True}
        
        # DB初期化
        self._initialize_db()
        
        self.logger.info("Knowledge base initialized")
    
    def _initialize_db(self):
        """データベースの初期化"""
        try:
            # DBに接続
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 事実テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 0.7,
                created_at TEXT,
                updated_at TEXT,
                category TEXT DEFAULT 'general',
                embedding_id INTEGER
            )
            ''')
            
            # 概念テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                confidence REAL DEFAULT 0.7,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # 概念定義テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER,
                definition TEXT NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 0.7,
                created_at TEXT,
                FOREIGN KEY (concept_id) REFERENCES concepts (id) ON DELETE CASCADE
            )
            ''')
            
            # 関係テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_concept_id INTEGER,
                target_concept_id INTEGER,
                relation_type TEXT NOT NULL,
                description TEXT,
                confidence REAL DEFAULT 0.7,
                created_at TEXT,
                FOREIGN KEY (source_concept_id) REFERENCES concepts (id) ON DELETE CASCADE,
                FOREIGN KEY (target_concept_id) REFERENCES concepts (id) ON DELETE CASCADE
            )
            ''')
            
            # 埋め込みテーブルの作成（ベクトル検索用）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector BLOB,  -- ベクトルをバイナリで保存
                created_at TEXT
            )
            ''')
            
            # 検索履歴テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_count INTEGER,
                timestamp TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def store_fact(self, content: str, source: Optional[str] = None, confidence: float = 0.7, 
                  category: str = "general") -> int:
        """
        新しい事実を知識ベースに保存
        
        Args:
            content: 事実の内容
            source: 情報ソース
            confidence: 信頼度 (0.0-1.0)
            category: カテゴリ
            
        Returns:
            新しい事実のID
        """
        try:
            # 重複チェック
            if self._is_duplicate_fact(content):
                self.logger.info(f"Duplicate fact detected: {content[:50]}...")
                return self._get_fact_id(content)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute(
                '''
                INSERT INTO facts (content, source, confidence, created_at, updated_at, category)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (content, source, confidence, now, now, category)
            )
            
            fact_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored new fact (ID: {fact_id})")
            return fact_id
            
        except Exception as e:
            self.logger.error(f"Error storing fact: {str(e)}")
            return -1
    
    def store_concept(self, name: str, description: Optional[str] = None, 
                     definitions: Optional[List[Dict[str, Any]]] = None,
                     confidence: float = 0.7) -> int:
        """
        新しい概念を知識ベースに保存
        
        Args:
            name: 概念名
            description: 概念の簡単な説明
            definitions: 概念の定義リスト
            confidence: 信頼度 (0.0-1.0)
            
        Returns:
            新しい概念のID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # まず概念自体を保存
            try:
                cursor.execute(
                    '''
                    INSERT INTO concepts (name, description, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (name, description, confidence, now, now)
                )
                concept_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # 既に存在する概念の場合はIDを取得
                cursor.execute("SELECT id FROM concepts WHERE name=?", (name,))
                concept_id = cursor.fetchone()[0]
                
                # 説明を更新
                if description:
                    cursor.execute(
                        "UPDATE concepts SET description=?, updated_at=? WHERE id=?",
                        (description, now, concept_id)
                    )
            
            # 定義を保存
            if definitions:
                for definition in definitions:
                    cursor.execute(
                        '''
                        INSERT INTO concept_definitions 
                        (concept_id, definition, source, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        ''',
                        (
                            concept_id, 
                            definition.get("content", ""),
                            definition.get("source", ""),
                            definition.get("confidence", 0.7),
                            now
                        )
                    )
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored concept: {name} (ID: {concept_id})")
            return concept_id
            
        except Exception as e:
            self.logger.error(f"Error storing concept: {str(e)}")
            return -1
    
    def store_relation(self, source_concept: str, target_concept: str, relation_type: str,
                      description: Optional[str] = None, confidence: float = 0.7) -> int:
        """
        概念間の関係を保存
        
        Args:
            source_concept: 始点の概念名
            target_concept: 終点の概念名
            relation_type: 関係タイプ (e.g. "is_a", "part_of", "related_to")
            description: 関係の説明
            confidence: 信頼度 (0.0-1.0)
            
        Returns:
            新しい関係のID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 概念IDの取得（存在しない場合は作成）
            source_id = self._get_or_create_concept_id(cursor, source_concept)
            target_id = self._get_or_create_concept_id(cursor, target_concept)
            
            now = datetime.now().isoformat()
            
            cursor.execute(
                '''
                INSERT INTO relations 
                (source_concept_id, target_concept_id, relation_type, description, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (source_id, target_id, relation_type, description, confidence, now)
            )
            
            relation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored relation: {source_concept} {relation_type} {target_concept} (ID: {relation_id})")
            return relation_id
            
        except Exception as e:
            self.logger.error(f"Error storing relation: {str(e)}")
            return -1
    
    def search_knowledge(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        知識ベースを検索
        
        Args:
            query: 検索クエリ
            limit: 各カテゴリの最大結果数
            
        Returns:
            検索結果（事実、概念、関係を含む辞書）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 結果を辞書として取得
            cursor = conn.cursor()
            
            # 検索履歴に記録
            cursor.execute(
                "INSERT INTO search_history (query, timestamp) VALUES (?, ?)",
                (query, datetime.now().isoformat())
            )
            
            # クエリからキーワードを抽出
            keywords = self._extract_keywords(query)
            search_pattern = "%"
            if keywords:
                search_pattern = "%" + "%".join(keywords) + "%"
            
            # 事実を検索
            cursor.execute(
                "SELECT * FROM facts WHERE content LIKE ? ORDER BY confidence DESC LIMIT ?",
                (search_pattern, limit)
            )
            facts = [dict(row) for row in cursor.fetchall()]
            
            # 概念を検索
            cursor.execute(
                '''
                SELECT c.*, GROUP_CONCAT(d.definition, '|') as definitions, 
                       GROUP_CONCAT(d.source, '|') as definition_sources,
                       GROUP_CONCAT(d.confidence, '|') as definition_confidences
                FROM concepts c
                LEFT JOIN concept_definitions d ON c.id = d.concept_id
                WHERE c.name LIKE ? OR c.description LIKE ?
                GROUP BY c.id
                ORDER BY c.confidence DESC
                LIMIT ?
                ''',
                (search_pattern, search_pattern, limit)
            )
            
            concepts = []
            for row in cursor.fetchall():
                concept = dict(row)
                
                # 複数の定義を分割して加工
                if concept.get('definitions'):
                    definitions = []
                    def_texts = concept['definitions'].split('|')
                    def_sources = concept.get('definition_sources', '').split('|') if concept.get('definition_sources') else []
                    def_confidences = concept.get('definition_confidences', '').split('|') if concept.get('definition_confidences') else []
                    
                    for i, text in enumerate(def_texts):
                        if text:
                            def_item = {"content": text}
                            if i < len(def_sources) and def_sources[i]:
                                def_item["source"] = def_sources[i]
                            if i < len(def_confidences) and def_confidences[i]:
                                try:
                                    def_item["confidence"] = float(def_confidences[i])
                                except ValueError:
                                    def_item["confidence"] = 0.7
                            definitions.append(def_item)
                    
                    concept['definitions'] = definitions
                    
                # 不要なフィールドを削除
                concept.pop('definition_sources', None)
                concept.pop('definition_confidences', None)
                
                concepts.append(concept)
            
            # 関係を検索（関連する概念名を含む）
            cursor.execute(
                '''
                SELECT r.*, sc.name as source_name, tc.name as target_name
                FROM relations r
                JOIN concepts sc ON r.source_concept_id = sc.id
                JOIN concepts tc ON r.target_concept_id = tc.id
                WHERE sc.name LIKE ? OR tc.name LIKE ? OR r.description LIKE ?
                ORDER BY r.confidence DESC
                LIMIT ?
                ''',
                (search_pattern, search_pattern, search_pattern, limit)
            )
            relations = [dict(row) for row in cursor.fetchall()]
            
            # 検索履歴を更新（結果数を記録）
            result_count = len(facts) + len(concepts) + len(relations)
            cursor.execute(
                "UPDATE search_history SET result_count=? WHERE id=(SELECT MAX(id) FROM search_history)",
                (result_count,)
            )
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Searched knowledge for '{query}', found {result_count} results")
            
            return {
                "facts": facts,
                "concepts": concepts,
                "relations": relations,
                "query": query,
                "total_results": result_count
            }
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {str(e)}")
            return {"facts": [], "concepts": [], "relations": [], "query": query, "total_results": 0}
    
    def update_confidence(self, item_type: str, item_id: int, confidence: float) -> bool:
        """
        知識項目の信頼度を更新
        
        Args:
            item_type: 項目タイプ ("fact", "concept", "relation")
            item_id: 項目ID
            confidence: 新しい信頼度 (0.0-1.0)
            
        Returns:
            更新が成功したかどうか
        """
        try:
            if confidence < 0.0 or confidence > 1.0:
                self.logger.warning(f"Invalid confidence value: {confidence}")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            if item_type == "fact":
                cursor.execute(
                    "UPDATE facts SET confidence=?, updated_at=? WHERE id=?",
                    (confidence, now, item_id)
                )
            elif item_type == "concept":
                cursor.execute(
                    "UPDATE concepts SET confidence=?, updated_at=? WHERE id=?",
                    (confidence, now, item_id)
                )
            elif item_type == "relation":
                cursor.execute(
                    "UPDATE relations SET confidence=? WHERE id=?",
                    (confidence, item_id)
                )
            else:
                self.logger.warning(f"Unknown item type: {item_type}")
                conn.close()
                return False
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected > 0:
                self.logger.info(f"Updated confidence for {item_type} ID {item_id} to {confidence}")
                return True
            else:
                self.logger.warning(f"No {item_type} found with ID {item_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error updating confidence: {str(e)}")
            return False
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        知識ベースの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 事実の数
            cursor.execute("SELECT COUNT(*) FROM facts")
            facts_count = cursor.fetchone()[0]
            
            # 概念の数
            cursor.execute("SELECT COUNT(*) FROM concepts")
            concepts_count = cursor.fetchone()[0]
            
            # 関係の数
            cursor.execute("SELECT COUNT(*) FROM relations")
            relations_count = cursor.fetchone()[0]
            
            # 定義の数
            cursor.execute("SELECT COUNT(*) FROM concept_definitions")
            definitions_count = cursor.fetchone()[0]
            
            # カテゴリ別の事実数
            cursor.execute(
                "SELECT category, COUNT(*) as count FROM facts GROUP BY category"
            )
            categories = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 平均信頼度
            cursor.execute("SELECT AVG(confidence) FROM facts")
            facts_avg_confidence = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(confidence) FROM concepts")
            concepts_avg_confidence = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(confidence) FROM relations")
            relations_avg_confidence = cursor.fetchone()[0] or 0
            
            # 検索履歴の統計
            cursor.execute("SELECT COUNT(*) FROM search_history")
            search_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(result_count) FROM search_history WHERE result_count IS NOT NULL")
            avg_search_results = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "facts_count": facts_count,
                "concepts_count": concepts_count,
                "relations_count": relations_count,
                "definitions_count": definitions_count,
                "total_items": facts_count + concepts_count + relations_count,
                "categories": categories,
                "average_confidence": {
                    "facts": facts_avg_confidence,
                    "concepts": concepts_avg_confidence,
                    "relations": relations_avg_confidence
                },
                "search_stats": {
                    "total_searches": search_count,
                    "average_results": avg_search_results
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting knowledge stats: {str(e)}")
            return {
                "facts_count": 0,
                "concepts_count": 0,
                "relations_count": 0,
                "total_items": 0,
                "error": str(e)
            }
    
    def export_knowledge(self, output_file: str = "knowledge_export.json") -> bool:
        """
        知識ベースをJSON形式でエクスポート
        
        Args:
            output_file: 出力ファイルパス
            
        Returns:
            エクスポートが成功したかどうか
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 事実の取得
            cursor.execute("SELECT * FROM facts")
            facts = [dict(row) for row in cursor.fetchall()]
            
            # 概念と定義の取得
            cursor.execute(
                '''
                SELECT c.*, GROUP_CONCAT(d.id) as def_ids, 
                       GROUP_CONCAT(d.definition) as definitions,
                       GROUP_CONCAT(d.source) as sources, 
                       GROUP_CONCAT(d.confidence) as confidences,
                       GROUP_CONCAT(d.created_at) as def_created_ats
                FROM concepts c
                LEFT JOIN concept_definitions d ON c.id = d.concept_id
                GROUP BY c.id
                '''
            )
            
            concepts = {}
            for row in cursor.fetchall():
                concept = dict(row)
                concept_id = concept["id"]
                
                # 定義情報の処理
                definitions = []
                if concept.get("def_ids") and concept.get("definitions"):
                    def_ids = str(concept["def_ids"]).split(",")
                    def_texts = str(concept["definitions"]).split(",")
                    def_sources = str(concept.get("sources", "")).split(",") if concept.get("sources") else []
                    def_confs = str(concept.get("confidences", "")).split(",") if concept.get("confidences") else []
                    def_dates = str(concept.get("def_created_ats", "")).split(",") if concept.get("def_created_ats") else []
                    
                    for i in range(len(def_ids)):
                        if i < len(def_texts):
                            def_item = {"id": int(def_ids[i]), "content": def_texts[i]}
                            
                            if i < len(def_sources) and def_sources[i]:
                                def_item["source"] = def_sources[i]
                                
                            if i < len(def_confs) and def_confs[i]:
                                try:
                                    def_item["confidence"] = float(def_confs[i])
                                except ValueError:
                                    def_item["confidence"] = 0.7
                                    
                            if i < len(def_dates) and def_dates[i]:
                                def_item["created_at"] = def_dates[i]
                                
                            definitions.append(def_item)
                
                # 概念情報の整理
                concept_info = {
                    "id": concept_id,
                    "name": concept["name"],
                    "confidence": concept["confidence"],
                    "created_at": concept["created_at"],
                    "updated_at": concept["updated_at"],
                    "definitions": definitions
                }
                
                if concept.get("description"):
                    concept_info["description"] = concept["description"]
                
                concepts[concept_id] = concept_info
            
            # 関係の取得
            cursor.execute(
                '''
                SELECT r.*, sc.name as source_name, tc.name as target_name
                FROM relations r
                JOIN concepts sc ON r.source_concept_id = sc.id
                JOIN concepts tc ON r.target_concept_id = tc.id
                '''
            )
            relations = [dict(row) for row in cursor.fetchall()]
            
            # 知識データをまとめる
            knowledge_data = {
                "facts": facts,
                "concepts": concepts,
                "relations": relations,
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "facts_count": len(facts),
                    "concepts_count": len(concepts),
                    "relations_count": len(relations)
                }
            }
            
            # JSONとして保存
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            
            conn.close()
            
            self.logger.info(f"Exported knowledge to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting knowledge: {str(e)}")
            return False
    
    def import_knowledge(self, input_file: str) -> Dict[str, int]:
        """
        JSONから知識ベースにデータをインポート
        
        Args:
            input_file: 入力ファイルパス
            
        Returns:
            インポート統計情報
        """
        try:
            if not os.path.exists(input_file):
                self.logger.error(f"Import file not found: {input_file}")
                return {"status": "error", "message": "File not found"}
            
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # インポート統計
            stats = {
                "facts_imported": 0,
                "concepts_imported": 0,
                "relations_imported": 0
            }
            
            # 事実のインポート
            for fact in data.get("facts", []):
                content = fact.get("content")
                if content:
                    self.store_fact(
                        content=content,
                        source=fact.get("source"),
                        confidence=fact.get("confidence", 0.7),
                        category=fact.get("category", "general")
                    )
                    stats["facts_imported"] += 1
            
            # 概念のインポート
            concepts_id_map = {}  # 元のID→新しいIDのマッピング
            
            for concept_id, concept in data.get("concepts", {}).items():
                name = concept.get("name")
                if name:
                    definitions = []
                    for def_item in concept.get("definitions", []):
                        if isinstance(def_item, dict) and "content" in def_item:
                            definitions.append(def_item)
                    
                    new_id = self.store_concept(
                        name=name,
                        description=concept.get("description"),
                        definitions=definitions,
                        confidence=concept.get("confidence", 0.7)
                    )
                    
                    if new_id > 0:
                        concepts_id_map[int(concept_id)] = new_id
                        stats["concepts_imported"] += 1
            
            # 関係のインポート
            for relation in data.get("relations", []):
                source_name = relation.get("source_name")
                target_name = relation.get("target_name")
                relation_type = relation.get("relation_type")
                
                if source_name and target_name and relation_type:
                    relation_id = self.store_relation(
                        source_concept=source_name,
                        target_concept=target_name,
                        relation_type=relation_type,
                        description=relation.get("description"),
                        confidence=relation.get("confidence", 0.7)
                    )
                    
                    if relation_id > 0:
                        stats["relations_imported"] += 1
            
            self.logger.info(f"Imported knowledge: {stats}")
            return {
                "status": "success", 
                **stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error importing knowledge: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_or_create_concept_id(self, cursor, concept_name: str) -> int:
        """概念名からIDを取得（存在しない場合は作成）"""
        cursor.execute("SELECT id FROM concepts WHERE name=?", (concept_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # 新しい概念を作成
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO concepts (name, created_at, updated_at) VALUES (?, ?, ?)",
                (concept_name, now, now)
            )
            return cursor.lastrowid
    
    def _is_duplicate_fact(self, content: str) -> bool:
        """内容が既存の事実と重複しているかチェック"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 完全一致をチェック
        cursor.execute("SELECT COUNT(*) FROM facts WHERE content=?", (content,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def _get_fact_id(self, content: str) -> int:
        """内容から事実のIDを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM facts WHERE content=?", (content,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else -1
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストから検索キーワードを抽出"""
        # 簡易的な実装
        # 文字列をスペースやカンマなどで分割し、長すぎる/短すぎる単語を除外
        words = re.findall(r'\b\w{3,20}\b', text.lower())
        
        # ストップワードの除外
        stopwords = {"and", "or", "the", "is", "are", "in", "on", "at", "to", "for", "with", "by",
                   "about", "like", "that", "this", "these", "those", "from", "as", "of"}
        keywords = [w for w in words if w not in stopwords]
        
        return keywords
