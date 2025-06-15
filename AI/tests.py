# tests.py - 测试模块
import unittest
import json
import os
from unittest.mock import patch, MagicMock

# 设置测试环境变量
os.environ["APP_ENV"] = "testing"

from recommendation_system import (
    get_recommendations, 
    load_user_history,
    build_prompt,
    evaluate_recommendations
)
from ranking import CoarseRanker, FineRanker, DiversityRanker, rerank_with_diversity
from explainability import FreshRecommendationExplainer
from config import current_config
from utils import load_json, save_json, SimpleCache

class TestRecommendationSystem(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.test_history = [
            {
                "product_name": "有机苹果",
                "timestamp": "2024-01-10",
                "category": "水果",
                "product_type": "新鲜水果",
                "price": 15.0,
                "rating": 9.5
            },
            {
                "product_name": "新鲜三文鱼",
                "timestamp": "2024-01-05",
                "category": "海鲜",
                "product_type": "冷冻海鲜",
                "price": 80.0,
                "rating": 9.0
            }
        ]
        
        self.test_recommendation = {
            "product_name": "有机苹果",
            "category": "水果",
            "product_type": "新鲜水果",
            "price": 15.0
        }
        
        # 创建临时测试文件
        self.test_file = "test_history.json"
        with open(self.test_file, "w") as f:
            json.dump({"history_projects": self.test_history}, f)
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_load_user_history(self):
        """测试用户历史加载功能"""
        history = load_user_history(self.test_file)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["product_name"], "有机苹果")
        self.assertTrue("time_since_last_project" in history[0])
    
    def test_build_prompt(self):
        """测试提示词构建功能"""
        prompt = build_prompt(self.test_history)
        self.assertIsInstance(prompt, str)
        self.assertIn("有机苹果", prompt)
        self.assertIn("新鲜三文鱼", prompt)
    
    def test_evaluate_recommendations(self):
        """测试推荐评估功能"""
        recommendations = [self.test_recommendation]
        score = evaluate_recommendations(recommendations, self.test_history)
        self.assertGreater(score, 0)
    
    @patch('recommendation_system.multi_model_predict')
    def test_get_recommendations_mock(self, mock_predict):
        """使用模拟数据测试推荐系统"""
        # 模拟LLM输出
        mock_predict.return_value = [json.dumps({
            "predicted_projects": [
                {
                    "product_name": "有机蔬菜礼盒",
                    "category": "蔬菜",
                    "product_type": "礼盒装",
                    "price": 50.0
                }
            ]
        })]
        
        # 调用推荐函数
        result = get_recommendations(self.test_file)
        
        # 验证结果
        self.assertIn("recommendations", result)
        self.assertIn("evaluation_score", result)
        self.assertEqual(len(result["recommendations"]), 1)

class TestRanking(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.user_features = [0.5, 0.3, 0.2]
        self.candidates = [
            {
                "product_name": "有机苹果",
                "category": "水果",
                "product_type": "新鲜水果",
                "price": 15.0,
                "features": [0.4, 0.3, 0.2]
            },
            {
                "product_name": "新鲜三文鱼",
                "category": "海鲜",
                "product_type": "冷冻海鲜",
                "price": 80.0,
                "features": [0.1, 0.8, 0.5]
            }
        ]
    
    def test_coarse_ranker(self):
        """测试粗排序功能"""
        ranker = CoarseRanker(self.user_features)
        ranked = ranker.rank(self.candidates)
        self.assertEqual(ranked[0]["product_name"], "有机苹果")
    
    def test_fine_ranker(self):
        """测试精排序功能"""
        user_prefs = {"price_range": 0.7, "category": 0.3}
        ranker = FineRanker(user_prefs)
        ranked = ranker.rank(self.candidates)
        self.assertEqual(ranked[0]["product_name"], "新鲜三文鱼")
    
    def test_diversity_ranker(self):
        """测试多样性排序功能"""
        already_selected = [{
            "product_name": "有机苹果",
            "category": "水果",
            "product_type": "新鲜水果",
            "price": 15.0
        }]
        
        ranker = DiversityRanker()
        best, remaining = ranker.rank(self.candidates, already_selected)
        self.assertEqual(best[0]["product_name"], "新鲜三文鱼")
    
    def test_rerank_with_diversity(self):
        """测试多样性重排序功能"""
        candidates = self.candidates * 3  # 复制候选项
        diverse = rerank_with_diversity(candidates, top_k=3)
        self.assertLessEqual(len(diverse), 3)

class TestExplainability(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.user_history = [
            {
                "product_name": "有机苹果",
                "timestamp": "2024-01-10",
                "category": "水果",
                "product_type": "新鲜水果",
                "price": 15.0
            }
        ]
        
        self.recommendation = {
            "product_name": "有机蔬菜礼盒",
            "category": "蔬菜",
            "product_type": "礼盒装",
            "price": 50.0
        }
    
    def test_generate_explanation(self):
        """测试解释生成功能"""
        explainer = FreshRecommendationExplainer(self.user_history)
        explanation = explainer.generate_explanation(self.recommendation)
        
        self.assertIn("recommendation", explanation)
        self.assertIn("reasons", explanation)
        self.assertTrue(len(explanation["reasons"]) > 0)

class TestUtils(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.test_data = {"test": "data"}
        self.test_file = "test_utils.json"
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_load_save_json(self):
        """测试JSON加载和保存功能"""
        # 保存测试
        result = save_json(self.test_data, self.test_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_file))
        
        # 加载测试
        loaded = load_json(self.test_file)
        self.assertEqual(loaded, self.test_data)
    
    def test_simple_cache(self):
        """测试缓存功能"""
        cache = SimpleCache(timeout=1)
        
        # 设置缓存
        cache.set("test_key", "test_value")
        
        # 获取缓存
        value = cache.get("test_key")
        self.assertEqual(value, "test_value")
        
        # 清除缓存
        cache.clear()
        value = cache.get("test_key")
        self.assertIsNone(value)

if __name__ == '__main__':
    unittest.main()