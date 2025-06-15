# recommendation_system.py - 推荐系统核心模块
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from config import current_config
from utils import load_json, save_json, setup_logger, calculate_time_since, SimpleCache
from ranking import CoarseRanker, FineRanker, rerank_with_diversity
from explainability import FreshRecommendationExplainer, RecommendationExplainer

# 设置日志
logger = setup_logger("recommendation_system", current_config.LOG_LEVEL)

# 创建缓存
if current_config.CACHE_ENABLED:
    cache = SimpleCache(timeout=current_config.CACHE_TIMEOUT)
else:
    cache = None

def multi_model_predict(prompt: str, model_name: str = None) -> List[str]:
    """使用多模型进行预测
    
    在实际应用中，这个函数会调用LLM API
    在测试环境下，返回模拟数据
    
    Args:
        prompt: 提示词
        model_name: 模型名称
    
    Returns:
        预测结果列表
    """
    if not model_name:
        model_name = current_config.MODEL_NAME
    
    logger.info(f"使用模型 {model_name} 进行预测")
    
    # 测试环境下返回模拟数据
    if getattr(current_config, "TESTING", False) or getattr(current_config, "USE_MOCK_DATA", False):
        logger.debug("使用模拟数据")
        return [json.dumps({
            "predicted_projects": [
                {
                    "project_type": "Web应用开发",
                    "tech_stack": ["JavaScript", "React", "Node.js"],
                    "project_size": "medium",
                    "confidence": 0.92
                },
                {
                    "project_type": "移动应用开发",
                    "tech_stack": ["Flutter", "Dart"],
                    "project_size": "medium",
                    "confidence": 0.85
                },
                {
                    "project_type": "数据分析",
                    "tech_stack": ["Python", "Pandas", "Matplotlib"],
                    "project_size": "small",
                    "confidence": 0.78
                }
            ]
        })]
    
    # 在实际环境中，这里会调用OpenAI API
    # 示例代码（实际应用时取消注释）：
    """
    import openai
    
    openai.api_key = current_config.OPENAI_API_KEY
    
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个软件项目推荐助手。请根据用户历史项目推荐新项目。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return [response.choices[0].message.content]
    except Exception as e:
        logger.error(f"API调用失败: {str(e)}")
        return []
    """
    
    # 临时返回空结果
    logger.warning("API调用功能尚未实现，返回空结果")
    return []

def load_user_history(history_file: str) -> List[Dict]:
    """加载并预处理用户历史数据
    
    Args:
        history_file: 历史数据文件路径
    
    Returns:
        处理后的用户历史列表
    """
    logger.info(f"加载用户历史: {history_file}")
    
    # 从缓存获取
    if cache:
        cached_history = cache.get(f"history_{history_file}")
        if cached_history:
            logger.debug("使用缓存的用户历史")
            return cached_history
    
    try:
        data = load_json(history_file)
        
        # 提取历史项目列表
        if "history_projects" in data:
            history = data["history_projects"]
        else:
            history = []
            
        # 预处理历史数据
        for project in history:
            # 添加时间信息
            if "timestamp" in project:
                days = calculate_time_since(project["timestamp"])
                project["time_since_last_project"] = days
            
            # 确保所有必要字段存在
            if "tech_stack" not in project:
                project["tech_stack"] = []
                
            if "project_size" not in project:
                project["project_size"] = "medium"
        
        # 按时间排序（最近的在前）
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 缓存结果
        if cache:
            cache.set(f"history_{history_file}", history)
            
        return history
    
    except Exception as e:
        logger.error(f"加载用户历史失败: {str(e)}")
        return []

def build_prompt(user_history: List[Dict]) -> str:
    """根据用户历史构建提示词
    
    Args:
        user_history: 用户历史数据
    
    Returns:
        构建的提示词
    """
    logger.info("构建推荐提示词")
    
    prompt = "根据以下用户历史项目，推荐3-5个新的软件项目：\n\n"
    
    for idx, project in enumerate(user_history, 1):
        prompt += f"项目{idx}:\n"
        prompt += f"- 类型: {project.get('project_type', '未知')}\n"
        prompt += f"- 技术栈: {', '.join(project.get('tech_stack', []))}\n"
        prompt += f"- 项目大小: {project.get('project_size', '未知')}\n"
        if "rating" in project:
            prompt += f"- 满意度评分: {project.get('rating')}/10\n"
        if "time_since_last_project" in project:
            prompt += f"- 完成于: {project.get('time_since_last_project')}天前\n"
        prompt += "\n"
    
    prompt += """请以JSON格式返回推荐结果，格式如下:
{
  "predicted_projects": [
    {
      "project_type": "项目类型",
      "tech_stack": ["技术1", "技术2"],
      "project_size": "项目大小(small/medium/large)",
      "confidence": 0.95
    }
  ]
}
"""
    
    return prompt

def extract_recommendations(model_output: List[str]) -> List[Dict]:
    """从模型输出中提取推荐
    
    Args:
        model_output: 模型输出字符串列表
    
    Returns:
        提取的推荐列表
    """
    logger.info("从模型输出提取推荐")
    
    if not model_output:
        logger.warning("模型输出为空")
        return []
    
    recommendations = []
    
    for output in model_output:
        try:
            # 尝试解析JSON
            data = json.loads(output)
            
            if "predicted_projects" in data:
                recommendations.extend(data["predicted_projects"])
            
        except json.JSONDecodeError:
            logger.error(f"无法解析模型输出为JSON: {output[:100]}...")
            
            # 尝试查找JSON部分
            try:
                import re
                json_match = re.search(r'({.*})', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                    if "predicted_projects" in data:
                        recommendations.extend(data["predicted_projects"])
            except Exception:
                logger.error("尝试提取JSON失败")
    
    # 过滤低置信度推荐
    filtered_recommendations = []
    for rec in recommendations:
        if "confidence" in rec and rec["confidence"] >= current_config.MIN_CONFIDENCE_SCORE:
            filtered_recommendations.append(rec)
        elif "confidence" not in rec:
            # 如果没有置信度字段，默认添加
            rec["confidence"] = 0.75
            filtered_recommendations.append(rec)
    
    # 限制推荐数量
    return filtered_recommendations[:current_config.MAX_RECOMMENDATIONS]

def evaluate_recommendations(recommendations: List[Dict], user_history: List[Dict]) -> float:
    """评估推荐结果质量
    
    Args:
        recommendations: 推荐列表
        user_history: 用户历史
    
    Returns:
        评估分数
    """
    logger.info(f"评估{len(recommendations)}个推荐")
    
    if not recommendations or not user_history:
        return 0.0
    
    total_score = 0.0
    
    # 提取用户偏好
    user_tech_stack = set()
    project_types = []
    project_sizes = []
    
    for project in user_history:
        if "tech_stack" in project:
            user_tech_stack.update(project.get("tech_stack", []))
        if "project_type" in project:
            project_types.append(project["project_type"])
        if "project_size" in project:
            project_sizes.append(project["project_size"])
    
    # 评估每个推荐
    for rec in recommendations:
        rec_score = 0.0
        
        # 技术栈匹配度
        if "tech_stack" in rec:
            rec_tech = set(rec.get("tech_stack", []))
            if rec_tech and user_tech_stack:
                overlap = len(rec_tech.intersection(user_tech_stack))
                tech_score = overlap / len(rec_tech) * 0.5
                rec_score += tech_score
        
        # 项目类型多样性
        if "project_type" in rec:
            if rec["project_type"] not in project_types:
                rec_score += 0.3  # 奖励新类型
            else:
                rec_score += 0.1  # 奖励熟悉类型
        
        # 项目大小适合度
        if "project_size" in rec:
            if rec["project_size"] in project_sizes:
                rec_score += 0.2
        
        # 考虑推荐的置信度
        if "confidence" in rec:
            rec_score *= rec["confidence"]
        
        total_score += rec_score
    
    # 归一化分数
    avg_score = total_score / len(recommendations)
    # 调整到1-10分
    final_score = avg_score * 10
    
    return final_score

class FreshRecommendationSystem:
    """生鲜推荐系统核心模块"""
    
    def __init__(self, user_history: List[Dict]):
        """初始化推荐系统
        
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
    
    def generate_recommendations(self) -> List[Dict]:
        """生成生鲜产品推荐
        
        Returns:
            推荐产品列表
        """
        # 构建用户特征向量
        user_features = self._build_user_features()
        
        # 获取候选产品
        candidates = self._get_candidate_products()
        
        # 粗排序
        coarse_ranker = CoarseRanker(user_features)
        ranked_candidates = coarse_ranker.rank(candidates)
        
        # 精排序
        user_prefs = {
            "price_range": 0.4,
            "product_type": 0.3,
            "category": 0.3
        }
        fine_ranker = FineRanker(user_prefs)
        ranked_candidates = fine_ranker.rank(ranked_candidates)
        
        # 增加多样性
        diverse_recommendations = rerank_with_diversity(
            ranked_candidates, 
            top_k=current_config.MAX_RECOMMENDATIONS
        )
        
        return diverse_recommendations
    
    def _build_user_features(self) -> List[float]:
        """构建用户特征向量
        
        Returns:
            用户特征向量
        """
        # 计算用户对不同类别和类型产品的偏好
        category_prefs = {}
        type_prefs = {}
        total_items = len(self.user_history)
        
        for product in self.user_history:
            category = product.get("category")
            product_type = product.get("product_type")
            
            category_prefs[category] = category_prefs.get(category, 0) + 1
            type_prefs[product_type] = type_prefs.get(product_type, 0) + 1
        
        # 归一化偏好
        category_prefs = {k: v / total_items for k, v in category_prefs.items()}
        type_prefs = {k: v / total_items for k, v in type_prefs.items()}
        
        # 构建特征向量
        features = [
            max(category_prefs.values(), default=0),  # 最喜欢的类别偏好
            max(type_prefs.values(), default=0),      # 最喜欢的类型偏好
            sum([p.get("price", 0) for p in self.user_history]) / total_items,  # 平均价格
            len(set([p.get("category") for p in self.user_history])) / 10,  # 类别多样性
            len(set([p.get("product_type") for p in self.user_history])) / 10  # 类型多样性
        ]
        
        return features
    
    def _get_candidate_products(self) -> List[Dict]:
        """获取候选产品列表
        
        Returns:
            候选产品列表
        """
        # 这里应该调用产品数据库或API获取候选产品
        # 为了演示，我们使用模拟数据
        candidates = [
            {
                "product_name": "有机苹果",
                "category": "水果",
                "product_type": "新鲜水果",
                "price": 15.0,
                "features": [0.8, 0.3, 15.0, 0.2, 0.1]
            },
            {
                "product_name": "新鲜三文鱼",
                "category": "海鲜",
                "product_type": "冷冻海鲜",
                "price": 80.0,
                "features": [0.3, 0.8, 80.0, 0.1, 0.2]
            },
            {
                "product_name": "有机蔬菜礼盒",
                "category": "蔬菜",
                "product_type": "礼盒装",
                "price": 50.0,
                "features": [0.5, 0.5, 50.0, 0.3, 0.1]
            }
        ]
        
        return candidates

def get_recommendations(history_file: str, user_id: str = None) -> Dict:
    """获取生鲜产品推荐
    
    Args:
        history_file: 用户历史数据文件路径
        user_id: 用户ID (可选)
    
    Returns:
        包含推荐和评估的结果字典
    """
    logger.info(f"为用户{user_id or '(未知)'}获取推荐")
    
    # 加载用户历史
    user_history = load_user_history(history_file)
    
    if not user_history:
        logger.warning("用户历史为空，无法生成推荐")
        return {
            "recommendations": [],
            "evaluation_score": 0,
            "total_count": 0
        }
    
    # 初始化推荐系统
    recommender = FreshRecommendationSystem(user_history)
    
    # 生成推荐
    recommendations = recommender.generate_recommendations()
    
    if not recommendations:
        logger.warning("未能生成有效推荐")
        return {
            "recommendations": [],
            "evaluation_score": 0,
            "total_count": 0
        }
    
    # 生成解释
    explainer = FreshRecommendationExplainer(user_history)
    explained_recommendations = explainer.generate_batch_explanations(recommendations)
    
    # 评估推荐质量
    eval_score = evaluate_recommendations(recommendations, user_history)
    
    # 返回结果
    return {
        "recommendations": explained_recommendations,
        "evaluation_score": eval_score,
        "total_count": len(explained_recommendations)
    }
