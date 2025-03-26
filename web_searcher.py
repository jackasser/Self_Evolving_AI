"""
Web検索モジュール

インターネットから情報を検索するためのコンポーネント。
複数の検索エンジンとAPIをサポートし、情報の取得と前処理を行う。
"""

import requests
import json
import logging
import re
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus

class WebSearcher:
    """
    Web検索機能を提供するクラス
    複数の検索エンジンをサポートし、レート制限を考慮
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        WebSearcherの初期化
        
        Args:
            config_path: 設定ファイルへのパス
        """
        self.logger = logging.getLogger("web_searcher")
        
        # 設定を読み込む
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                self.config = config.get("web_search", {})
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {str(e)}。デフォルト設定を使用します。")
            self.config = {}
        
        # 検索履歴
        self.search_history = []
        
        # レート制限トラッキング
        self.rate_limits = {
            "last_request_time": 0,
            "requests_in_last_minute": 0,
            "requests_in_last_hour": 0,
            "cooldown_until": 0
        }
        
        # 検索エンジン設定
        self.engines = {
            "duckduckgo": {
                "enabled": self.config.get("use_duckduckgo", True),
                "url": "https://api.duckduckgo.com/",
                "delay": 1.0  # リクエスト間の最小遅延（秒）
            },
            "wikipedia": {
                "enabled": self.config.get("use_wikipedia", True),
                "url": "https://ja.wikipedia.org/w/api.php",
                "delay": 1.0
            }
        }
        
        # デフォルトのユーザーエージェント
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        self.logger.info("Web searcher initialized")
    
    def search(self, query: str, max_results: int = 5, engines: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Webで情報を検索
        
        Args:
            query: 検索クエリ
            max_results: 取得する最大結果数
            engines: 使用する検索エンジンのリスト（省略時は全て）
            
        Returns:
            検索結果
        """
        # レート制限のチェック
        if not self._check_rate_limits():
            self.logger.warning("Rate limit exceeded, search aborted")
            return {
                "status": "error",
                "message": "レート制限を超えました。しばらく待ってから再試行してください。",
                "query": query,
                "results": []
            }
        
        self.logger.info(f"Searching for: {query}")
        
        # 検索エンジンの選択
        if not engines:
            engines = [name for name, config in self.engines.items() if config["enabled"]]
        else:
            # 指定されたエンジンのうち、有効なもののみを使用
            engines = [name for name in engines if name in self.engines and self.engines[name]["enabled"]]
        
        if not engines:
            self.logger.warning("No search engines available")
            return {
                "status": "error",
                "message": "利用可能な検索エンジンがありません。",
                "query": query,
                "results": []
            }
        
        # 検索の実行
        all_results = []
        errors = []
        
        for engine in engines:
            try:
                self.logger.debug(f"Searching with {engine}")
                
                if engine == "duckduckgo":
                    results = self._search_duckduckgo(query, max_results)
                elif engine == "wikipedia":
                    results = self._search_wikipedia(query, max_results)
                else:
                    self.logger.warning(f"Unknown search engine: {engine}")
                    continue
                
                self.logger.debug(f"Found {len(results)} results with {engine}")
                all_results.extend(results)
                
                # レート制限のために少し待機
                time.sleep(self.engines[engine]["delay"])
                
            except Exception as e:
                error_msg = f"Error searching with {engine}: {str(e)}"
                self.logger.error(error_msg)
                errors.append({"engine": engine, "error": str(e)})
        
        # 結果の重複除去とランク付け
        unique_results = self._remove_duplicates(all_results)
        ranked_results = self._rank_results(unique_results, query)
        
        # 結果数を制限
        final_results = ranked_results[:max_results]
        
        # 検索履歴に記録
        search_record = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "engines_used": engines,
            "results_count": len(final_results),
            "errors": errors
        }
        self.search_history.append(search_record)
        
        # レート制限カウンターを更新
        self._update_rate_limits()
        
        return {
            "status": "success" if not errors else "partial_success",
            "query": query,
            "results": final_results,
            "total_found": len(all_results),
            "returned": len(final_results),
            "errors": errors if errors else None
        }
    
    def get_article_content(self, url: str) -> Dict[str, Any]:
        """
        記事の内容を取得
        
        Args:
            url: 記事のURL
            
        Returns:
            記事の内容と関連情報
        """
        # レート制限のチェック
        if not self._check_rate_limits():
            self.logger.warning("Rate limit exceeded, content fetch aborted")
            return {
                "status": "error",
                "message": "レート制限を超えました。しばらく待ってから再試行してください。",
                "url": url
            }
        
        self.logger.info(f"Fetching article content from: {url}")
        
        try:
            # URLパターンに基づいて処理を分岐
            if "wikipedia.org" in url:
                content = self._fetch_wikipedia_article(url)
            else:
                content = self._fetch_generic_article(url)
            
            # レート制限カウンターを更新
            self._update_rate_limits()
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error fetching article content: {str(e)}")
            return {
                "status": "error",
                "message": f"記事の取得中にエラーが発生しました: {str(e)}",
                "url": url
            }
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        検索統計情報を取得
        
        Returns:
            検索統計
        """
        if not self.search_history:
            return {
                "total_searches": 0,
                "rate_limits": self.rate_limits
            }
        
        # 最近の検索数
        now = time.time()
        searches_last_hour = sum(1 for s in self.search_history 
                               if (now - datetime.fromisoformat(s["timestamp"]).timestamp()) < 3600)
        
        searches_last_day = sum(1 for s in self.search_history 
                              if (now - datetime.fromisoformat(s["timestamp"]).timestamp()) < 86400)
        
        # エンジン別の使用回数
        engine_usage = {}
        for search in self.search_history:
            for engine in search.get("engines_used", []):
                if engine not in engine_usage:
                    engine_usage[engine] = 1
                else:
                    engine_usage[engine] += 1
        
        # 平均結果数
        avg_results = sum(s.get("results_count", 0) for s in self.search_history) / len(self.search_history)
        
        # エラー率
        error_count = sum(1 for s in self.search_history if s.get("errors"))
        error_rate = error_count / len(self.search_history) if self.search_history else 0
        
        return {
            "total_searches": len(self.search_history),
            "searches_last_hour": searches_last_hour,
            "searches_last_day": searches_last_day,
            "engine_usage": engine_usage,
            "average_results": avg_results,
            "error_rate": error_rate,
            "rate_limits": self.rate_limits
        }
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """DuckDuckGo検索を実行"""
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }
        
        response = requests.get(self.engines["duckduckgo"]["url"], params=params, headers=headers)
        
        if response.status_code != 200:
            self.logger.warning(f"DuckDuckGo API returned status code {response.status_code}")
            return []
        
        data = response.json()
        results = []
        
        # Abstract（要約）の追加
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Summary"),
                "content": data["Abstract"],
                "url": data.get("AbstractURL", ""),
                "source": "DuckDuckGo Abstract",
                "score": 1.0
            })
        
        # 関連トピックの追加
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in topic and "FirstURL" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                    "content": topic["Text"],
                    "url": topic["FirstURL"],
                    "source": "DuckDuckGo Related",
                    "score": 0.7
                })
            
            # ネストされたトピックの処理
            if "Topics" in topic:
                for subtopic in topic["Topics"]:
                    if "Text" in subtopic and "FirstURL" in subtopic:
                        results.append({
                            "title": subtopic.get("Text", "").split(" - ")[0] if " - " in subtopic.get("Text", "") else subtopic.get("Text", ""),
                            "content": subtopic["Text"],
                            "url": subtopic["FirstURL"],
                            "source": "DuckDuckGo Subtopic",
                            "score": 0.6
                        })
        
        return results
    
    def _search_wikipedia(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Wikipedia検索を実行"""
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "utf8": 1,
            "srlimit": max_results
        }
        
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }
        
        response = requests.get(self.engines["wikipedia"]["url"], params=params, headers=headers)
        
        if response.status_code != 200:
            self.logger.warning(f"Wikipedia API returned status code {response.status_code}")
            return []
        
        data = response.json()
        results = []
        
        for item in data.get("query", {}).get("search", []):
            # HTML タグを除去
            snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
            
            results.append({
                "title": item.get("title", ""),
                "content": snippet,
                "url": f"https://ja.wikipedia.org/wiki/{quote_plus(item.get('title', ''))}",
                "source": "Wikipedia",
                "score": 0.8,
                "page_id": item.get("pageid")
            })
        
        return results
    
    def _fetch_wikipedia_article(self, url: str) -> Dict[str, Any]:
        """Wikipediaの記事を取得"""
        # URLからページタイトルを抽出
        title_match = re.search(r'/wiki/([^/]+)$', url)
        if not title_match:
            return {
                "status": "error",
                "message": "Invalid Wikipedia URL format",
                "url": url
            }
        
        page_title = title_match.group(1)
        
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "extracts|info",
            "inprop": "url",
            "explaintext": 1,
            "exintro": 1  # 導入部のみを取得（長すぎるのを避けるため）
        }
        
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }
        
        response = requests.get(self.engines["wikipedia"]["url"], params=params, headers=headers)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Wikipedia API returned status code {response.status_code}",
                "url": url
            }
        
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        if not pages:
            return {
                "status": "error",
                "message": "No page found",
                "url": url
            }
        
        # 最初のページを取得（キーはページID）
        page = next(iter(pages.values()))
        
        if "missing" in page:
            return {
                "status": "error",
                "message": "Page does not exist",
                "url": url
            }
        
        return {
            "status": "success",
            "title": page.get("title", ""),
            "content": page.get("extract", ""),
            "url": page.get("fullurl", url),
            "source": "Wikipedia",
            "last_modified": page.get("touched"),
            "fetch_time": datetime.now().isoformat()
        }
    
    def _fetch_generic_article(self, url: str) -> Dict[str, Any]:
        """一般的なWebページから記事を取得"""
        # 実際の実装では、BeautifulSoupなどを使用してHTMLをパースし、
        # 主要コンテンツを抽出する必要があります。
        # ここでは、簡易的なモック実装を提供します。
        
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"HTTP status code: {response.status_code}",
                    "url": url
                }
            
            # 簡易的なタイトル抽出
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # 簡易的な内容抽出（実際のプロジェクトではより高度な抽出が必要）
            # メタディスクリプションの取得
            desc_match = re.search(r'<meta[^>]*name=["|\']description["|\'][^>]*content=["|\']([^>]*?)["|\'][^>]*>', 
                                 response.text, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # 記事の冒頭部分の抽出（簡易的）
            body_content = re.sub(r'<script.*?>.*?</script>', '', response.text, flags=re.DOTALL | re.IGNORECASE)
            body_content = re.sub(r'<style.*?>.*?</style>', '', body_content, flags=re.DOTALL | re.IGNORECASE)
            paragraphs = re.findall(r'<p>(.*?)</p>', body_content, re.DOTALL | re.IGNORECASE)
            
            content_text = []
            total_length = 0
            max_length = 2000  # 最大文字数
            
            for p in paragraphs:
                # HTMLタグを除去
                p_text = re.sub(r'<[^>]+>', '', p).strip()
                if p_text and len(p_text) > 20:  # 短すぎる段落は無視
                    content_text.append(p_text)
                    total_length += len(p_text)
                    if total_length > max_length:
                        break
            
            main_content = "\n\n".join(content_text)
            
            if not main_content and description:
                main_content = description
            
            return {
                "status": "success",
                "title": title,
                "description": description,
                "content": main_content,
                "url": url,
                "source": "Web Page",
                "fetch_time": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}",
                "url": url
            }
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複する検索結果を削除"""
        unique_results = []
        seen_urls = set()
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """検索結果をクエリの関連性でランク付け"""
        query_keywords = set(self._extract_keywords(query.lower()))
        
        for result in results:
            # 基本スコアを取得
            base_score = result.get("score", 0.5)
            
            # タイトルと内容の関連性を計算
            title_keywords = set(self._extract_keywords(result.get("title", "").lower()))
            content_keywords = set(self._extract_keywords(result.get("content", "").lower()))
            
            title_match = len(query_keywords.intersection(title_keywords)) / len(query_keywords) if query_keywords else 0
            content_match = len(query_keywords.intersection(content_keywords)) / len(query_keywords) if query_keywords else 0
            
            # ソースの信頼性係数
            source_trust = {
                "Wikipedia": 1.0,
                "DuckDuckGo Abstract": 0.9,
                "DuckDuckGo Related": 0.7,
                "Web Page": 0.6
            }
            
            source = result.get("source", "")
            trust_factor = source_trust.get(source, 0.5)
            
            # 最終スコアの計算
            final_score = (base_score * 0.3) + (title_match * 0.3) + (content_match * 0.2) + (trust_factor * 0.2)
            result["relevance_score"] = final_score
        
        # スコアでソート
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        # 簡易的な実装
        # 文字列をスペースやカンマなどで分割し、長すぎる/短すぎる単語を除外
        words = re.findall(r'\b\w{3,20}\b', text.lower())
        
        # ストップワードの除外
        stopwords = {"and", "or", "the", "is", "are", "in", "on", "at", "to", "for", "with", "by",
                   "about", "like", "that", "this", "these", "those", "from", "as", "of"}
        keywords = [w for w in words if w not in stopwords]
        
        return keywords
    
    def _check_rate_limits(self) -> bool:
        """レート制限をチェック"""
        now = time.time()
        
        # クールダウン期間中ならFalse
        if now < self.rate_limits["cooldown_until"]:
            return False
        
        # 1分あたりの最大リクエスト数を確認
        if now - self.rate_limits["last_request_time"] > 60:
            # 1分以上経過していれば、カウンターをリセット
            self.rate_limits["requests_in_last_minute"] = 0
        
        max_requests_per_minute = self.config.get("max_requests_per_minute", 10)
        if self.rate_limits["requests_in_last_minute"] >= max_requests_per_minute:
            # リクエスト過多でクールダウン
            self.rate_limits["cooldown_until"] = now + 60  # 1分間クールダウン
            self.logger.warning(f"Rate limit exceeded: {max_requests_per_minute} requests per minute")
            return False
        
        # 1時間あたりの最大リクエスト数を確認
        if now - self.rate_limits["last_request_time"] > 3600:
            # 1時間以上経過していれば、カウンターをリセット
            self.rate_limits["requests_in_last_hour"] = 0
        
        max_requests_per_hour = self.config.get("max_requests_per_hour", 100)
        if self.rate_limits["requests_in_last_hour"] >= max_requests_per_hour:
            # リクエスト過多でクールダウン
            self.rate_limits["cooldown_until"] = now + 600  # 10分間クールダウン
            self.logger.warning(f"Rate limit exceeded: {max_requests_per_hour} requests per hour")
            return False
        
        return True
    
    def _update_rate_limits(self) -> None:
        """レート制限カウンターを更新"""
        now = time.time()
        self.rate_limits["last_request_time"] = now
        self.rate_limits["requests_in_last_minute"] += 1
        self.rate_limits["requests_in_last_hour"] += 1
