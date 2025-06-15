# explainability.py - 推荐解释模块
from typing import Dict, List, Any
import logging
from utils import setup_logger

logger = setup_logger("explainability")

class FreshRecommendationExplainer:
    """生鲜推荐结果解释生成器"""
    
    def __init__(self, user_history: List[Dict]):
        """初始化解释生成器
        
        Args:
            user_history: 用户历史数据列表
        """
        self.user_history = user_history
        self.patterns = {
            "product_type": {
                "same": "基于您之前购买过的{value}类型产品",
                "new": "尝试新的{value}类型产品，扩展您的购物体验"
            },
            "category": {
                "same": "继续选择您熟悉的{value}类别",
                "new": "探索{value}类别，发现更多新鲜好物"
            },
            "price_range": {
                "same": "继续选择您熟悉的{value}价格范围",
                "new": "尝试{value}价格范围的产品，享受不同层次的购物体验"
            }
        }
    
    def generate_explanation(self, recommendation: Dict) -> Dict:
        """为推荐项生成解释
        
        Args:
            recommendation: 推荐项数据
            
        Returns:
            包含推荐项和解释的字典
        """
        logger.info(f"为推荐项生成解释: {recommendation['product_name']}")
        
        reasons = []
        
        # 分析产品类型
        reasons.append(self._analyze_feature(
            "product_type", 
            recommendation["product_type"]
        ))
        
        # 分析类别
        category_reason = self._analyze_feature("category", recommendation["category"])
        if category_reason:
            reasons.append(category_reason)
        
        # 分析价格范围
        price_reason = self._analyze_feature("price_range", recommendation["price_range"])
        if price_reason:
            reasons.append(price_reason)
        
        # 增加通用推荐理由
        if len(reasons) < 2:
            reasons.append("这个产品符合您的购物习惯和偏好")
        
        return {
            "recommendation": recommendation,
            "reasons": reasons
        }
    
    def _analyze_feature(self, feature_name: str, feature_value: Any) -> str:
        """分析特征与用户历史的关系，生成解释
        
        Args:
            feature_name: 特征名称
            feature_value: 特征值
            
        Returns:
            特征解释字符串
        """
        # 检查是否在用户历史中存在
        is_familiar = False
        
        for product in self.user_history:
            if product.get(feature_name) == feature_value:
                is_familiar = True
                break
        
        # 根据熟悉程度选择不同的解释模板
        pattern_key = "same" if is_familiar else "new"
        
        # 填充模板
        if feature_name == "price_range":
            range_map = {"low": "低价", "medium": "中价", "high": "高价"}
            display_value = range_map.get(feature_value, feature_value)
        else:
            display_value = feature_value
            
        return self.patterns[feature_name][pattern_key].format(value=display_value)
    
    def generate_batch_explanations(self, recommendations: List[Dict]) -> List[Dict]:
        """为多个推荐项生成解释
        
        Args:
            recommendations: 推荐项列表
            
        Returns:
            包含解释的推荐项列表
        """
        logger.info(f"为{len(recommendations)}个推荐项生成批量解释")
        return [self.generate_explanation(rec) for rec in recommendations]