#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自己成長型AI（Self-Evolving AI）のテストランナー
すべてのテストを実行し、結果をレポートします。
"""

import unittest
import sys
import os
import time

# 色付きの出力用
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def run_tests():
    """すべてのテストを実行"""
    # テスト開始メッセージ
    print(f"\n{Colors.HEADER}{Colors.BOLD}自己成長型AI（Self-Evolving AI）テスト実行{Colors.ENDC}\n")
    print(f"開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # テスト対象のリスト
    test_modules = [
        'test_goal_manager',
        'test_self_feedback',
        # 他のテストモジュールを追加
    ]
    
    # テスト結果の集計
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_time = 0
    
    # 各テストの実行
    for module in test_modules:
        print(f"\n{Colors.BOLD}テストモジュール: {module}{Colors.ENDC}")
        
        start_time = time.time()
        
        # テストローダーとランナーの準備
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module)
        runner = unittest.TextTestRunner(verbosity=2)
        
        # テスト実行
        result = runner.run(suite)
        
        # 結果の集計
        duration = time.time() - start_time
        total_time += duration
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        # 結果の表示
        status = f"{Colors.OKGREEN}成功{Colors.ENDC}" if result.wasSuccessful() else f"{Colors.FAIL}失敗{Colors.ENDC}"
        print(f"結果: {status} ({duration:.2f}秒)")
    
    # 総合結果の表示
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}テスト総合結果:{Colors.ENDC}")
    print(f"実行テスト数: {total_tests}")
    print(f"失敗: {total_failures}")
    print(f"エラー: {total_errors}")
    print(f"合計実行時間: {total_time:.2f}秒")
    
    overall_status = "成功" if total_failures == 0 and total_errors == 0 else "失敗"
    status_color = Colors.OKGREEN if overall_status == "成功" else Colors.FAIL
    print(f"総合判定: {status_color}{overall_status}{Colors.ENDC}")
    print("=" * 60)
    
    # 終了コードの設定（失敗があれば非ゼロを返す）
    return 0 if overall_status == "成功" else 1

if __name__ == '__main__':
    sys.exit(run_tests())
