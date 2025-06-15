# ranking.py - 推荐排序模块
import numpy as np
from typing import List, Dict, Tuple, Any
import logging
from utils import setup_logger
from config import current_config

logger = setup_logger("ranking")

class CoarseRanker:
    """粗排序器 - 使用基于向量相似度的排序"""
    
    def __init__(self, user_features: List[float]):
        """初始化粗排序器
        
        Args:
            user_features: 用户特征向量
        """
        self.user_features = np.array(user_features)
        logger.info(f"初始化粗排序器，用户特征维度: {len(user_features)}")
    
    def rank(self, candidates: List[Dict]) -> List[Dict]:
        """对候选项进行排序
        
        Args:
            candidates: 候选推荐项列表
            
        Returns:
            排序后的候选项列表
        """
        if not candidates:
            return []
            
        # 计算每个候选项与用户特征的相似度
        scores = []
        for item in candidates:
            if "features" not in item:
                # 如果没有特征向量，给予最低分数
                scores.append(0.0)
                continue
                
            item_features = np.array(item["features"])
            # 使用余弦相似度
            similarity = self._cosine_similarity(self.user_features, item_features)
            scores.append(similarity)
        
        # 根据分数排序
        sorted_indices = np.argsort(scores)[::-1]  # 降序排列
        return [candidates[i] for i in sorted_indices]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            余弦相似度
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)

class FineRanker:
    """精排序器 - 使用加权特征进行排序"""
    
    def __init__(self, user_preferences: Dict[str, float]):
        """初始化精排序器
        
        Args:
            user_preferences: 用户偏好权重
        """
        self.user_preferences = user_preferences
        logger.info(f"初始化精排序器，用户偏好: {user_preferences}")
    
    def rank(self, candidates: List[Dict]) -> List[Dict]:
        """对候选项进行排序
        
        Args:
            candidates: 候选推荐项列表
            
        Returns:
            排序后的候选项列表
        """
        if not candidates:
            return []
            
        # 计算每个候选项的加权分数
        for item in candidates:
            item["_score"] = self._calculate_score(item)
        
        # 根据分数排序
        sorted_candidates = sorted(candidates, key=lambda x: x["_score"], reverse=True)
        
        # 移除临时分数字段
        for item in sorted_candidates:
            if "_score" in item:
                del item["_score"]
                
        return sorted_candidates
    
    def _calculate_score(self, item: Dict) -> float:
        """计算候选项的加权分数
        
        Args:
            item: 候选项
            
        Returns:
            加权分数
        """
        score = 0.0
        
        # 根据用户偏好对特征加权
        for feature, weight in self.user_preferences.items():
            if feature in item:
                # 简单特征匹配
                if isinstance(item[feature], (str, int, float, bool)):
                    score += weight
                # 列表特征部分匹配 (如技术栈)
                elif isinstance(item[feature], list) and item[feature]:
                    score += weight * 0.5  # 部分匹配给予部分分数
        
        return score

class DiversityRanker:
    """多样性排序器 - 增加推荐结果的多样性"""
    
    def __init__(self):
        """初始化多样性排序器"""
        logger.info("初始化多样性排序器")
    
    def rank(self, candidates: List[Dict], already_selected: List[Dict] = None) -> Tuple[List[Dict], List[Dict]]:
        """选择多样性最大的候选项
        
        Args:
            candidates: 候选推荐项列表
            already_selected: 已选择的项目列表
            
        Returns:
            (选中的候选项, 剩余的候选项)
        """
        if not candidates:
            return [], []
            
        if not already_selected:
            already_selected = []
            
        # 计算每个候选项与已选项的多样性分数
        diversity_scores = []
        
        for item in candidates:
            # 如果已选列表为空，给所有候选项相同的分数
            if not already_selected:
                diversity_scores.append(1.0)
                continue
                
            # 计算与已选项的差异性
            avg_similarity = self._calculate_avg_similarity(item, already_selected)
            # 多样性分数 = 1 - 相似度
            diversity_scores.append(1.0 - avg_similarity)
        
        # 选择多样性最高的项
        best_idx = np.argmax(diversity_scores)
        selected = [candidates[best_idx]]
        
        # 返回选中的和未选中的
        remaining = candidates.copy()
        remaining.pop(best_idx)
        
        return selected, remaining
    
    def _calculate_avg_similarity(self, item: Dict, selected_items: List[Dict]) -> float:
        """计算项目与已选项的平均相似度
        
        Args:
            item: 候选项
            selected_items: 已选择的项目列表
            
        Returns:
            平均相似度
        """
        similarities = []
        
        for selected in selected_items:
            sim = self._calculate_similarity(item, selected)
            similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_similarity(self, item1: Dict, item2: Dict) -> float:
        """计算两个项目间的相似度
        
        Args:
            item1: 第一个项目
            item2: 第二个项目
            
        Returns:
            相似度分数
        """
        similarity = 0.0
        total_weight = 0.0
        
        # 项目类型相似度
        if "project_type" in item1 and "project_type" in item2:
            weight = 0.5
            if item1["project_type"] == item2["project_type"]:
                similarity += weight
            total_weight += weight
        
        # 技术栈相似度
        if "tech_stack" in item1 and "tech_stack" in item2:
            weight = 0.3
            tech1 = set(item1["tech_stack"])
            tech2 = set(item2["tech_stack"])
            
            if tech1 and tech2:  # 确保不是空集
                # Jaccard相似度
                intersection = len(tech1.intersection(tech2))
                union = len(tech1.union(tech2))
                tech_sim = intersection / union if union > 0 else 0
                similarity += weight * tech_sim
            
            total_weight += weight
        
        # 项目大小相似度
        if "project_size" in item1 and "project_size" in item2:
            weight = 0.2
            if item1["project_size"] == item2["project_size"]:
                similarity += weight
            total_weight += weight
        
        # 归一化相似度
        return similarity / total_weight if total_weight > 0 else 0.0

def rerank_with_diversity(candidates: List[Dict], top_k: int = 5) -> List[Dict]:
    """使用多样性策略重新排序候选项
    
    Args:
        candidates: 候选推荐项列表
        top_k: 返回的最大项目数
        
    Returns:
        多样化排序后的候选项列表
    """
    if not candidates:
        return []
        
    logger.info(f"使用多样性策略重排序{len(candidates)}个候选项")
    
    ranker = DiversityRanker()
    selected = []
    remaining = candidates.copy()
    
    # 迭代选择多样性最大的项
    for _ in range(min(top_k, len(candidates))):
        if not remaining:
            break
            
        picked, remaining = ranker.rank(remaining, selected)
        selected.extend(picked)
    
    return selected
