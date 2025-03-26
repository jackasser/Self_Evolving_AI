import logging
import json
import time
import re
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import urllib.request
import urllib.error
import urllib.parse
import ssl
from http.client import HTTPResponse
import html
from html.parser import HTMLParser
import hashlib

class WebKnowledgeFetcher:
    """
    インターネットから情報を取得し、知識ベースを拡張するためのコンポーネント。
    ウェブ検索、コンテンツ抽出、情報の評価と統合を行う。
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        WebKnowledgeFetcherの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        # 設定を読み込む
        with open(config_path, "r", encoding='utf-8') as f:
            config = json.load(f)
        
        self.config = config.get("web_knowledge", {})
        self.logger = logging.getLogger("web_knowledge_fetcher")
        
        # アクセス履歴
        self.access_history = []
        
        # 情報のキャッシュ
        self.content_cache = {}
        
        # 信頼できるドメインのリスト
        self.trusted_domains = self.config.get("trusted_domains", [
            "wikipedia.org",
            "github.com",
            "arxiv.org",
            "scholar.google.com",
            "nature.com",
            "science.org",
            "research.gov",
            "education.gov",
            "stackoverflow.com",
            "docs.python.org"
        ])
        
        # 制限パラメータ
        self.rate_limit = self.config.get("rate_limit", {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "requests_per_day": 500
        })
        
        # 現在の利用状況
        self.usage_stats = {
            "minute": {"count": 0, "reset_time": time.time() + 60},
            "hour": {"count": 0, "reset_time": time.time() + 3600},
            "day": {"count": 0, "reset_time": time.time() + 86400}
        }
        
        # ユーザーエージェントのローテーション（サイトに負荷をかけないため）
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
        ]
        
        # HTML解析のためのパーサー
        self.html_parser = HTMLContentParser()
        
        # SSL コンテキスト
        self.ssl_context = ssl.create_default_context()
        
        self.logger.info("Web knowledge fetcher initialized")
    
    def search_information(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        インターネットで情報を検索
        
        Args:
            query: 検索クエリ
            max_results: 取得する最大結果数
            
        Returns:
            検索結果のリスト
        """
        # レート制限をチェック
        if not self._check_rate_limits():
            self.logger.warning("Rate limit exceeded, search aborted")
            return []
        
        self.logger.info(f"Searching information for: {query}")
        
        # 検索クエリのサニタイズ
        sanitized_query = self._sanitize_query(query)
        
        try:
            # 検索結果のフェッチ（実際の実装ではAPIを使用）
            # この例では簡略化のため、モック検索結果を生成
            search_results = self._mock_search_results(sanitized_query, max_results)
            
            # 検索統計の更新
            self._update_usage_stats()
            
            # アクセス履歴に記録
            self.access_history.append({
                "type": "search",
                "query": sanitized_query,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(search_results)
            })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error during information search: {str(e)}")
            return []
    
    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        指定されたURLからコンテンツを取得
        
        Args:
            url: 取得するコンテンツのURL
            
        Returns:
            取得したコンテンツの情報
        """
        # URLの検証
        if not self._is_safe_url(url):
            self.logger.warning(f"Unsafe URL requested: {url}")
            return {
                "status": "error",
                "message": "Unsafe URL requested",
                "url": url
            }
        
        # レート制限をチェック
        if not self._check_rate_limits():
            self.logger.warning("Rate limit exceeded, fetch aborted")
            return {
                "status": "error",
                "message": "Rate limit exceeded",
                "url": url
            }
        
        # キャッシュをチェック
        cache_key = self._get_cache_key(url)
        if cache_key in self.content_cache:
            self.logger.info(f"Returning cached content for URL: {url}")
            return self.content_cache[cache_key]
        
        self.logger.info(f"Fetching content from URL: {url}")
        
        try:
            # コンテンツの取得
            content, status_code, headers = self._fetch_url(url)
            
            # コンテンツの解析
            if status_code == 200:
                content_type = headers.get("Content-Type", "").lower()
                
                if "text/html" in content_type:
                    # HTMLコンテンツの場合
                    parsed_content = self.html_parser.parse(content)
                    content_text = parsed_content.get("text", "")
                    title = parsed_content.get("title", "")
                    
                elif "application/json" in content_type:
                    # JSONコンテンツの場合
                    try:
                        parsed_json = json.loads(content)
                        content_text = json.dumps(parsed_json, indent=2)
                        title = url.split("/")[-1]
                    except json.JSONDecodeError:
                        content_text = content
                        title = url.split("/")[-1]
                        
                elif "text/plain" in content_type:
                    # プレーンテキストの場合
                    content_text = content
                    title = url.split("/")[-1]
                    
                else:
                    # その他のコンテンツタイプ
                    content_text = f"[Unsupported content type: {content_type}]"
                    title = url.split("/")[-1]
                
                # 結果の作成
                result = {
                    "status": "success",
                    "url": url,
                    "title": title,
                    "content": content_text[:10000],  # 長すぎるコンテンツを切り詰め
                    "content_type": content_type,
                    "fetch_time": datetime.now().isoformat(),
                    "metadata": {
                        "length": len(content),
                        "domain": urllib.parse.urlparse(url).netloc
                    }
                }
                
                # キャッシュに保存
                self.content_cache[cache_key] = result
                
                # 使用統計を更新
                self._update_usage_stats()
                
                # アクセス履歴に記録
                self.access_history.append({
                    "type": "fetch",
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                
                return result
            else:
                # エラーレスポンスの場合
                result = {
                    "status": "error",
                    "url": url,
                    "message": f"HTTP error: {status_code}",
                    "fetch_time": datetime.now().isoformat()
                }
                
                self.logger.warning(f"Failed to fetch content, HTTP status: {status_code}")
                
                # アクセス履歴に記録
                self.access_history.append({
                    "type": "fetch",
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": f"HTTP error: {status_code}"
                })
                
                return result
        
        except Exception as e:
            self.logger.error(f"Error fetching content from {url}: {str(e)}")
            
            # アクセス履歴に記録
            self.access_history.append({
                "type": "fetch",
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            
            return {
                "status": "error",
                "url": url,
                "message": f"Error: {str(e)}",
                "fetch_time": datetime.now().isoformat()
            }
    
    def extract_knowledge(self, content: Dict[str, Any], query: str = None) -> Dict[str, Any]:
        """
        取得したコンテンツから知識を抽出
        
        Args:
            content: 取得したコンテンツ情報
            query: オリジナルのクエリ（関連性判断に使用）
            
        Returns:
            抽出された知識
        """
        if content.get("status") != "success":
            return {
                "status": "error",
                "message": "Cannot extract knowledge from errored content",
                "original_error": content.get("message")
            }
        
        self.logger.info(f"Extracting knowledge from content: {content.get('title', '')}")
        
        try:
            # コンテンツテキストの取得
            content_text = content.get("content", "")
            
            # 知識の抽出（実際の実装ではNLPなどを使用）
            # この例では簡略化のため、テキストの最初の部分を取得
            
            # 抽出するセクションの特定
            sections = self._split_into_sections(content_text)
            
            # クエリに関連するセクションの選択
            if query:
                relevant_sections = self._get_relevant_sections(sections, query)
            else:
                relevant_sections = sections[:3]  # 最初の3セクションを取得
            
            # 知識項目の抽出
            knowledge_items = []
            
            for section in relevant_sections:
                # セクションから知識項目を抽出
                items = self._extract_knowledge_items(section)
                knowledge_items.extend(items)
            
            # 重複の除去
            unique_items = self._remove_duplicates(knowledge_items)
            
            # 関連性でソート（クエリがある場合）
            if query:
                sorted_items = self._sort_by_relevance(unique_items, query)
            else:
                sorted_items = unique_items
            
            # 最大項目数に制限
            final_items = sorted_items[:20]  # 最大20項目
            
            result = {
                "status": "success",
                "source": content.get("url"),
                "title": content.get("title"),
                "knowledge_items": final_items,
                "extraction_time": datetime.now().isoformat(),
                "query": query
            }
            
            self.logger.info(f"Extracted {len(final_items)} knowledge items")
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting knowledge: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting knowledge: {str(e)}",
                "source": content.get("url")
            }
    
    def validate_information(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        抽出された知識の信頼性を検証
        
        Args:
            knowledge: 抽出された知識
            
        Returns:
            検証結果を含む知識
        """
        if knowledge.get("status") != "success":
            return knowledge
        
        self.logger.info(f"Validating information from: {knowledge.get('source', '')}")
        
        try:
            # ソースの信頼性評価
            source_url = knowledge.get("source", "")
            source_domain = urllib.parse.urlparse(source_url).netloc
            
            # 信頼スコアの計算
            trust_score = self._calculate_trust_score(source_domain, knowledge)
            
            # 各知識項目の検証
            validated_items = []
            
            for item in knowledge.get("knowledge_items", []):
                # 項目の検証（実際の実装ではより複雑な検証ロジックを使用）
                validation = self._validate_knowledge_item(item)
                
                # 検証結果を項目に追加
                validated_item = item.copy()
                validated_item["validation"] = validation
                validated_items.append(validated_item)
            
            # 検証結果の追加
            validated_knowledge = knowledge.copy()
            validated_knowledge["trust_score"] = trust_score
            validated_knowledge["knowledge_items"] = validated_items
            validated_knowledge["validation_time"] = datetime.now().isoformat()
            
            self.logger.info(f"Information validated with trust score: {trust_score:.2f}")
            return validated_knowledge
            
        except Exception as e:
            self.logger.error(f"Error validating information: {str(e)}")
            return {
                "status": "error",
                "message": f"Error validating information: {str(e)}",
                "source": knowledge.get("source")
            }
    
    def integrate_knowledge(self, validated_knowledge: Dict[str, Any], knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        検証済みの知識をAIの知識ベースに統合
        
        Args:
            validated_knowledge: 検証済みの知識
            knowledge_base: 現在の知識ベース
            
        Returns:
            更新された知識ベース
        """
        if validated_knowledge.get("status") != "success":
            return knowledge_base
        
        self.logger.info("Integrating new knowledge into knowledge base")
        
        try:
            # 知識ベースのコピーを作成
            updated_kb = knowledge_base.copy()
            
            # 信頼スコアのチェック
            trust_score = validated_knowledge.get("trust_score", 0.0)
            min_trust_score = self.config.get("min_trust_score", 0.7)
            
            if trust_score < min_trust_score:
                self.logger.warning(f"Knowledge not integrated due to low trust score: {trust_score:.2f}")
                return knowledge_base
            
            # 各知識項目を統合
            for item in validated_knowledge.get("knowledge_items", []):
                # 項目の検証結果をチェック
                if not item.get("validation", {}).get("is_valid", False):
                    continue
                
                # 項目の種類に基づいて統合
                item_type = item.get("type", "fact")
                
                if item_type == "fact":
                    self._integrate_fact(item, updated_kb)
                elif item_type == "concept":
                    self._integrate_concept(item, updated_kb)
                elif item_type == "method":
                    self._integrate_method(item, updated_kb)
                elif item_type == "relation":
                    self._integrate_relation(item, updated_kb)
            
            # 統合タイムスタンプを更新
            if "metadata" not in updated_kb:
                updated_kb["metadata"] = {}
            
            updated_kb["metadata"]["last_update"] = datetime.now().isoformat()
            updated_kb["metadata"]["update_source"] = validated_knowledge.get("source")
            
            # ファイルへの保存（オプション）
            if self.config.get("save_knowledge", False):
                knowledge_file = self.config.get("knowledge_file", "knowledge_base.json")
                with open(knowledge_file, "w", encoding='utf-8') as f:
                    json.dump(updated_kb, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Knowledge integration completed")
            return updated_kb
            
        except Exception as e:
            self.logger.error(f"Error integrating knowledge: {str(e)}")
            return knowledge_base
    
    def get_access_statistics(self) -> Dict[str, Any]:
        """
        情報アクセスの統計を取得
        
        Returns:
            アクセス統計情報
        """
        # 現在時刻
        now = time.time()
        
        # 過去24時間のアクセス
        day_ago = now - 86400
        recent_access = [a for a in self.access_history if datetime.fromisoformat(a["timestamp"]).timestamp() > day_ago]
        
        # 種類別のアクセス数
        access_by_type = {}
        for access in recent_access:
            access_type = access.get("type")
            if access_type not in access_by_type:
                access_by_type[access_type] = 0
            access_by_type[access_type] += 1
        
        # ステータス別のアクセス数
        access_by_status = {}
        for access in recent_access:
            status = access.get("status", "unknown")
            if status not in access_by_status:
                access_by_status[status] = 0
            access_by_status[status] += 1
        
        # 残りの利用可能リクエスト数
        remaining_requests = {
            "minute": self.rate_limit["requests_per_minute"] - self.usage_stats["minute"]["count"],
            "hour": self.rate_limit["requests_per_hour"] - self.usage_stats["hour"]["count"],
            "day": self.rate_limit["requests_per_day"] - self.usage_stats["day"]["count"]
        }
        
        # リセットまでの時間
        reset_times = {
            "minute": max(0, self.usage_stats["minute"]["reset_time"] - now),
            "hour": max(0, self.usage_stats["hour"]["reset_time"] - now),
            "day": max(0, self.usage_stats["day"]["reset_time"] - now)
        }
        
        stats = {
            "total_access": len(self.access_history),
            "recent_access": len(recent_access),
            "access_by_type": access_by_type,
            "access_by_status": access_by_status,
            "cache_size": len(self.content_cache),
            "rate_limits": {
                "remaining": remaining_requests,
                "reset_seconds": reset_times
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    
    def clear_cache(self) -> int:
        """
        コンテンツキャッシュをクリア
        
        Returns:
            クリアされたキャッシュエントリの数
        """
        cache_size = len(self.content_cache)
        self.content_cache = {}
        self.logger.info(f"Content cache cleared ({cache_size} entries)")
        return cache_size
    
    def _check_rate_limits(self) -> bool:
        """
        レート制限をチェック
        
        Returns:
            リクエストが許可されるかどうか
        """
        now = time.time()
        
        # タイマーのリセットをチェック
        for period in ["minute", "hour", "day"]:
            if now > self.usage_stats[period]["reset_time"]:
                self.usage_stats[period]["count"] = 0
                
                # 次のリセット時間を設定
                if period == "minute":
                    self.usage_stats[period]["reset_time"] = now + 60
                elif period == "hour":
                    self.usage_stats[period]["reset_time"] = now + 3600
                elif period == "day":
                    self.usage_stats[period]["reset_time"] = now + 86400
        
        # 制限をチェック
        if self.usage_stats["minute"]["count"] >= self.rate_limit["requests_per_minute"]:
            return False
        if self.usage_stats["hour"]["count"] >= self.rate_limit["requests_per_hour"]:
            return False
        if self.usage_stats["day"]["count"] >= self.rate_limit["requests_per_day"]:
            return False
        
        return True
    
    def _update_usage_stats(self) -> None:
        """
        使用統計を更新
        """
        for period in ["minute", "hour", "day"]:
            self.usage_stats[period]["count"] += 1
    
    def _is_safe_url(self, url: str) -> bool:
        """
        URLが安全かどうか確認
        
        Args:
            url: チェックするURL
            
        Returns:
            URLが安全かどうか
        """
        # URLの構文をチェック
        try:
            parsed_url = urllib.parse.urlparse(url)
        except:
            return False
        
        # スキームをチェック（HTTPSのみ許可）
        if parsed_url.scheme != "https":
            return False
        
        # ドメインをチェック
        domain = parsed_url.netloc
        
        # 信頼できるドメインかIPアドレスでないことを確認
        if not any(domain.endswith(trusted) for trusted in self.trusted_domains):
            return False
        
        # ローカルホストやプライベートIPをブロック
        if domain in ["localhost", "127.0.0.1", "0.0.0.0"] or \
           re.match(r"^192\.168\.", domain) or \
           re.match(r"^10\.", domain) or \
           re.match(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.", domain):
            return False
        
        return True
    
    def _sanitize_query(self, query: str) -> str:
        """
        検索クエリをサニタイズ
        
        Args:
            query: サニタイズするクエリ
            
        Returns:
            サニタイズされたクエリ
        """
        # 特殊文字の削除
        sanitized = re.sub(r'[^\w\s\-.,?]', '', query)
        
        # 長すぎるクエリの切り詰め
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _get_cache_key(self, url: str) -> str:
        """
        URLからキャッシュキーを生成
        
        Args:
            url: URL
            
        Returns:
            キャッシュキー
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def _fetch_url(self, url: str) -> Tuple[str, int, Dict[str, str]]:
        """
        URLからコンテンツを取得
        
        Args:
            url: 取得するURL
            
        Returns:
            コンテンツ、ステータスコード、ヘッダーのタプル
        """
        # 標準ライブラリではなく、モックデータを返す
        # 実際の実装では、requests などを使用してリクエストを行う
        
        # ダミーデータの生成
        content = f"<html><head><title>Page about {url}</title></head><body>"
        content += f"<h1>Information about the requested topic</h1>"
        content += f"<p>This is a mock response for the URL: {url}</p>"
        content += f"<p>The system is functioning in demonstration mode.</p>"
        content += f"<p>In a real implementation, this would contain actual web content.</p>"
        
        # URLからキーワードを抽出
        try:
            path = urllib.parse.urlparse(url).path
            keywords = path.split('/')[-1].replace('-', ' ').split('_')
            
            # キーワードに基づいたコンテンツを生成
            for keyword in keywords:
                if len(keyword) > 3:  # 短すぎるキーワードをスキップ
                    content += f"<h2>About {keyword}</h2>"
                    content += f"<p>{keyword.capitalize()} is an important concept in this domain.</p>"
                    content += f"<p>There are several aspects of {keyword} that are worth noting:</p>"
                    content += f"<ul>"
                    content += f"<li>The history of {keyword} dates back to its origins.</li>"
                    content += f"<li>{keyword.capitalize()} has evolved over time to include new methodologies.</li>"
                    content += f"<li>Modern applications of {keyword} include various fields.</li>"
                    content += f"</ul>"
        except:
            # URLの解析に失敗した場合は汎用コンテンツを生成
            content += f"<h2>General Information</h2>"
            content += f"<p>This page contains general information about the topic.</p>"
            content += f"<p>Key points to consider:</p>"
            content += f"<ul><li>Point 1</li><li>Point 2</li><li>Point 3</li></ul>"
        
        content += "</body></html>"
        
        # ステータスコードとヘッダーの生成
        status_code = 200
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(content)),
            "Server": "MockServer/1.0"
        }
        
        return content, status_code, headers
    
    def _mock_search_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        モック検索結果を生成（実際の実装では検索APIを使用）
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        # クエリの単語を分解
        words = query.lower().split()
        
        # 実際の検索の代わりにモック結果を生成
        results = []
        
        # 使用するドメインのセット
        domains = [
            "wikipedia.org",
            "github.com",
            "arxiv.org",
            "stackoverflow.com",
            "docs.python.org",
            "medium.com",
            "kaggle.com",
            "education.gov"
        ]
        
        for i in range(min(max_results, 10)):
            # ランダムなドメインを選択
            domain = random.choice(domains)
            
            # タイトルを生成
            title_words = random.sample(words, min(len(words), 3))
            extra_words = ["Guide", "Tutorial", "Introduction", "Overview", "Documentation", "Examples"]
            title = " ".join([word.capitalize() for word in title_words]) + " " + random.choice(extra_words)
            
            # 説明を生成
            description = f"A comprehensive resource about {' '.join(title_words)}. This page provides detailed information about the topic."
            
            # URLを生成
            url_path = "-".join(title_words)
            url = f"https://www.{domain}/article/{url_path}"
            
            result = {
                "title": title,
                "url": url,
                "description": description,
                "domain": domain,
                "relevance_score": 0.9 - (i * 0.1)  # 徐々に関連性を下げる
            }
            
            results.append(result)
        
        return results
    
    def _split_into_sections(self, text: str) -> List[str]:
        """
        テキストをセクションに分割
        
        Args:
            text: 分割するテキスト
            
        Returns:
            セクションのリスト
        """
        # 見出しパターンでテキストを分割
        sections = re.split(r'\n(?=[A-Z][A-Za-z\s]+:|\d+\.\s+[A-Z])', text)
        
        # 空のセクションを削除
        sections = [s.strip() for s in sections if s.strip()]
        
        # セクションが見つからない場合は段落で分割
        if len(sections) <= 1:
            sections = re.split(r'\n\s*\n', text)
            sections = [s.strip() for s in sections if s.strip()]
        
        return sections
    
    def _get_relevant_sections(self, sections: List[str], query: str) -> List[str]:
        """
        クエリに関連するセクションを取得
        
        Args:
            sections: セクションのリスト
            query: 検索クエリ
            
        Returns:
            関連するセクションのリスト
        """
        query_words = set(query.lower().split())
        
        # 各セクションの関連スコアを計算
        section_scores = []
        
        for section in sections:
            # 単語の一致数をカウント
            section_words = set(section.lower().split())
            matching_words = query_words.intersection(section_words)
            
            # スコアを計算
            score = len(matching_words) / len(query_words) if query_words else 0
            
            section_scores.append((section, score))
        
        # スコアで降順にソート
        section_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 上位のセクションを返す（最低でも1つ）
        relevant_sections = [s[0] for s in section_scores[:max(3, len(sections))]]
        
        if not relevant_sections:
            return sections[:1]
        
        return relevant_sections
    
    def _extract_knowledge_items(self, section: str) -> List[Dict[str, Any]]:
        """
        セクションから知識項目を抽出
        
        Args:
            section: テキストセクション
            
        Returns:
            抽出された知識項目のリスト
        """
        items = []
        
        # 文に分割
        sentences = re.split(r'(?<=[.!?])\s+', section)
        
        # 各文から知識を抽出
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 文の種類を判別
            item_type = self._determine_item_type(sentence)
            
            # 項目の作成
            item = {
                "content": sentence,
                "type": item_type,
                "confidence": 0.8,  # デフォルト値
                "extracted_from": section[:50] + "..." if len(section) > 50 else section
            }
            
            items.append(item)
        
        return items
    
    def _determine_item_type(self, sentence: str) -> str:
        """
        文の種類（事実、概念、方法、関係）を判別
        
        Args:
            sentence: 判別する文
            
        Returns:
            項目の種類
        """
        lower_sent = sentence.lower()
        
        # 定義パターン
        if re.search(r'is defined as|refers to|is a|are|means', lower_sent):
            return "concept"
        
        # 手順パターン
        if re.search(r'how to|steps|process|method|procedure|algorithm', lower_sent):
            return "method"
        
        # 関係パターン
        if re.search(r'relationship|related to|correlation|depends on|affects', lower_sent):
            return "relation"
        
        # デフォルトは事実
        return "fact"
    
    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複する知識項目を除去
        
        Args:
            items: 知識項目のリスト
            
        Returns:
            重複のない知識項目のリスト
        """
        unique_items = []
        content_set = set()
        
        for item in items:
            content = item["content"]
            
            # 既存の内容と類似していないか確認
            if content not in content_set:
                content_set.add(content)
                unique_items.append(item)
        
        return unique_items
    
    def _sort_by_relevance(self, items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        知識項目をクエリとの関連性でソート
        
        Args:
            items: ソートする知識項目のリスト
            query: 検索クエリ
            
        Returns:
            関連性でソートされた知識項目のリスト
        """
        query_words = set(query.lower().split())
        
        # 各項目の関連スコアを計算
        item_scores = []
        
        for item in items:
            content = item["content"].lower()
            content_words = set(content.split())
            
            # 単語の一致数をカウント
            matching_words = query_words.intersection(content_words)
            
            # スコアを計算
            score = len(matching_words) / len(query_words) if query_words else 0
            
            item_scores.append((item, score))
        
        # スコアで降順にソート
        item_scores.sort(key=lambda x: x[1], reverse=True)
        
        # ソートされた項目を返す
        return [item[0] for item in item_scores]
    
    def _calculate_trust_score(self, domain: str, knowledge: Dict[str, Any]) -> float:
        """
        情報源の信頼性スコアを計算
        
        Args:
            domain: ドメイン名
            knowledge: 抽出された知識
            
        Returns:
            信頼性スコア（0.0〜1.0）
        """
        # 基本スコア
        base_score = 0.5
        
        # 信頼できるドメインの場合はスコアを上げる
        if any(domain.endswith(trusted) for trusted in self.trusted_domains):
            base_score += 0.3
        
        # 特に高信頼なドメイン
        highly_trusted = ["wikipedia.org", "edu", "gov"]
        if any(domain.endswith(trusted) for trusted in highly_trusted):
            base_score += 0.1
        
        # コンテンツ特性に基づく調整
        items = knowledge.get("knowledge_items", [])
        
        # 項目数が多いほど信頼性は高い（ある程度まで）
        item_count = len(items)
        if item_count > 10:
            base_score += 0.05
        
        # 極端に矛盾する内容がないか確認
        contradictions = self._check_contradictions(items)
        if contradictions:
            base_score -= 0.1
        
        # スコアの範囲を制限
        return max(0.0, min(1.0, base_score))
    
    def _check_contradictions(self, items: List[Dict[str, Any]]) -> bool:
        """
        知識項目間の矛盾をチェック
        
        Args:
            items: チェックする知識項目のリスト
            
        Returns:
            矛盾が見つかったかどうか
        """
        # 実際の実装ではより高度な矛盾検出ロジックを使用
        # この例では簡略化のため、常にFalseを返す
        return False
    
    def _validate_knowledge_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        個々の知識項目を検証
        
        Args:
            item: 検証する知識項目
            
        Returns:
            検証結果
        """
        content = item["content"]
        
        # 基本的な検証ルール
        # 1. 長すぎないこと
        if len(content) > 500:
            return {
                "is_valid": False,
                "reason": "Content too long",
                "confidence": 0.7
            }
        
        # 2. 明らかな意見言語を含まないこと
        opinion_words = ["best", "worst", "greatest", "terrible", "amazing", "awesome", "horrible"]
        if any(word in content.lower() for word in opinion_words):
            return {
                "is_valid": False,
                "reason": "Contains opinion language",
                "confidence": 0.8
            }
        
        # 3. 誤解を招く可能性のある表現をチェック
        misleading_patterns = [
            r"all\s+[a-z]+\s+are",
            r"never",
            r"always",
            r"everyone",
            r"nobody"
        ]
        
        for pattern in misleading_patterns:
            if re.search(pattern, content.lower()):
                return {
                    "is_valid": False,
                    "reason": "Contains absolute or misleading language",
                    "confidence": 0.7
                }
        
        # デフォルトでは有効とする
        return {
            "is_valid": True,
            "confidence": 0.9
        }
    
    def _integrate_fact(self, item: Dict[str, Any], knowledge_base: Dict[str, Any]) -> None:
        """
        事実を知識ベースに統合
        
        Args:
            item: 統合する事実
            knowledge_base: 知識ベース
        """
        # 事実カテゴリを確保
        if "facts" not in knowledge_base:
            knowledge_base["facts"] = []
        
        # 事実の追加
        fact_entry = {
            "content": item["content"],
            "confidence": item.get("validation", {}).get("confidence", 0.5),
            "source": item.get("source", "unknown"),
            "added_at": datetime.now().isoformat()
        }
        
        knowledge_base["facts"].append(fact_entry)
    
    def _integrate_concept(self, item: Dict[str, Any], knowledge_base: Dict[str, Any]) -> None:
        """
        概念を知識ベースに統合
        
        Args:
            item: 統合する概念
            knowledge_base: 知識ベース
        """
        # 概念カテゴリを確保
        if "concepts" not in knowledge_base:
            knowledge_base["concepts"] = {}
        
        # 概念の追加（概念の名前を抽出）
        concept_match = re.search(r"([A-Za-z\s]+)\s+is\s+|([A-Za-z\s]+)\s+refers to\s+", item["content"])
        
        if concept_match:
            concept_name = (concept_match.group(1) or concept_match.group(2)).strip().lower()
            
            # 既存の概念を更新または新規作成
            if concept_name in knowledge_base["concepts"]:
                # 既存の定義に追加
                knowledge_base["concepts"][concept_name]["definitions"].append({
                    "content": item["content"],
                    "confidence": item.get("validation", {}).get("confidence", 0.5),
                    "source": item.get("source", "unknown"),
                    "added_at": datetime.now().isoformat()
                })
            else:
                # 新しい概念を作成
                knowledge_base["concepts"][concept_name] = {
                    "definitions": [{
                        "content": item["content"],
                        "confidence": item.get("validation", {}).get("confidence", 0.5),
                        "source": item.get("source", "unknown"),
                        "added_at": datetime.now().isoformat()
                    }],
                    "related_concepts": []
                }
        else:
            # 概念名が特定できない場合
            generic_key = f"concept_{len(knowledge_base['concepts'])}"
            knowledge_base["concepts"][generic_key] = {
                "definitions": [{
                    "content": item["content"],
                    "confidence": item.get("validation", {}).get("confidence", 0.5),
                    "source": item.get("source", "unknown"),
                    "added_at": datetime.now().isoformat()
                }],
                "related_concepts": []
            }
    
    def _integrate_method(self, item: Dict[str, Any], knowledge_base: Dict[str, Any]) -> None:
        """
        方法を知識ベースに統合
        
        Args:
            item: 統合する方法
            knowledge_base: 知識ベース
        """
        # 方法カテゴリを確保
        if "methods" not in knowledge_base:
            knowledge_base["methods"] = []
        
        # 方法の追加
        method_entry = {
            "content": item["content"],
            "confidence": item.get("validation", {}).get("confidence", 0.5),
            "source": item.get("source", "unknown"),
            "added_at": datetime.now().isoformat()
        }
        
        knowledge_base["methods"].append(method_entry)
    
    def _integrate_relation(self, item: Dict[str, Any], knowledge_base: Dict[str, Any]) -> None:
        """
        関係を知識ベースに統合
        
        Args:
            item: 統合する関係
            knowledge_base: 知識ベース
        """
        # 関係カテゴリを確保
        if "relations" not in knowledge_base:
            knowledge_base["relations"] = []
        
        # 関係の追加
        relation_entry = {
            "content": item["content"],
            "confidence": item.get("validation", {}).get("confidence", 0.5),
            "source": item.get("source", "unknown"),
            "added_at": datetime.now().isoformat()
        }
        
        knowledge_base["relations"].append(relation_entry)


class HTMLContentParser(HTMLParser):
    """
    HTMLコンテンツを解析するためのパーサー
    """
    
    def __init__(self):
        super().__init__()
        self.result = {"text": "", "title": ""}
        self.current_tag = None
        self.skip_data = False
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        
        # タイトルタグの処理
        if tag == "title":
            self.skip_data = False
        # スキップするタグ
        elif tag in ["script", "style", "iframe", "canvas", "svg", "noscript"]:
            self.skip_data = True
        
    def handle_endtag(self, tag):
        if tag == self.current_tag:
            self.current_tag = None
        
        if tag in ["script", "style", "iframe", "canvas", "svg", "noscript"]:
            self.skip_data = False
    
    def handle_data(self, data):
        if self.skip_data:
            return
        
        # テキストデータを追加
        if data.strip():
            if self.current_tag == "title":
                self.result["title"] = data.strip()
            else:
                self.result["text"] += data.strip() + " "
    
    def parse(self, html_content):
        """
        HTMLコンテンツを解析
        
        Args:
            html_content: 解析するHTMLコンテンツ
            
        Returns:
            解析結果（テキストとタイトル）
        """
        self.result = {"text": "", "title": ""}
        self.feed(html_content)
        self.result["text"] = self.result["text"].strip()
        
        # HTMLエンティティをデコード
        self.result["text"] = html.unescape(self.result["text"])
        if self.result["title"]:
            self.result["title"] = html.unescape(self.result["title"])
        
        return self.result
