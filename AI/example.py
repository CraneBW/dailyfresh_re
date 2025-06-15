# example.py - 示例用法
"""
本文件展示了生鲜购物网站推荐系统的使用方法和示例
"""

import json
from recommendation_system import get_recommendations
from ranking import rerank_with_diversity
from utils import setup_logger, timer_decorator

# 设置日志
logger = setup_logger("example", "INFO")

@timer_decorator
def basic_recommendation_example():
    """基本生鲜推荐示例"""
    logger.info("运行基本生鲜推荐示例...")
    
    # 获取推荐
    result = get_recommendations('user_history_example.json', "U-123456")
    
    # 输出推荐结果
    print("\n=== 基本生鲜推荐示例 ===")
    for idx, item in enumerate(result["recommendations"], 1):
        print(f"\n{idx}. {item['recommendation']['product_name']}")  # 修改为产品名称
        print(f"   类别: {item['recommendation']['category']}")     # 修改为产品类别
        print(f"   价格: {item['recommendation']['price']}元")      # 修改为价格
        print(f"   推荐理由: {' '.join(item['reasons'])}")
    
    print(f"\n推荐评估得分: {result['evaluation_score']:.2f}")
    print(f"总推荐数量: {result['total_count']}")
    
    return result

@timer_decorator
def diversity_recommendation_example():
    """多样性生鲜推荐示例"""
    logger.info("运行多样性生鲜推荐示例...")
    
    # 获取基本推荐
    result = get_recommendations('user_history_example.json')
    
    # 原始推荐列表
    original_recommendations = result["recommendations"]
    
    # 应用多样性重排序
    diverse_recommendations = rerank_with_diversity(
        [item["recommendation"] for item in original_recommendations], 
        top_k=3
    )
    
    # 输出结果比较
    print("\n=== 多样性生鲜推荐示例 ===")
    print("\n原始推荐的前3项：")
    product_names = [item["recommendation"]["product_name"] for item in original_recommendations[:3]]  # 修改为产品名称
    print(f"产品名称: {', '.join(product_names)}")
    
    print("\n多样性重排序后的3项：")
    diverse_names = [item["product_name"] for item in diverse_recommendations]  # 修改为产品名称
    print(f"产品名称: {', '.join(diverse_names)}")

@timer_decorator
def custom_user_history_example():
    """自定义用户历史示例"""
    logger.info("运行自定义用户历史示例...")
    
    # 创建自定义用户历史
    custom_history = {
        "user_id": "custom-user",
        "history_products": [  # 修改为历史产品
            {
                "product_name": "有机苹果",  # 修改为产品名称
                "timestamp": "2024-05-01",
                "category": "水果",          # 修改为类别
                "price": 15.0,               # 修改为价格
                "rating": 8.5
            },
            {
                "product_name": "新鲜三文鱼",  # 修改为产品名称
                "timestamp": "2024-04-15",
                "category": "海鲜",          # 修改为类别
                "price": 80.0,               # 修改为价格
                "rating": 9.0
            }
        ]
    }
    
    # 保存到临时文件
    temp_file = "custom_history.json"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(custom_history, f, ensure_ascii=False, indent=2)
    
    # 获取推荐
    result = get_recommendations(temp_file)
    
    # 输出推荐结果
    print("\n=== 自定义用户历史示例 ===")
    for idx, item in enumerate(result["recommendations"], 1):
        print(f"\n{idx}. {item['recommendation']['product_name']}")  # 修改为产品名称
        print(f"   类别: {item['recommendation']['category']}")     # 修改为类别
        print(f"   价格: {item['recommendation']['price']}元")      # 修改为价格
        print(f"   推荐理由: {' '.join(item['reasons'])}")
    
    # 清理临时文件
    import os
    os.remove(temp_file)

if __name__ == "__main__":
    print("生鲜购物网站推荐系统示例")
    print("=" * 50)
    
    # 运行示例
    basic_result = basic_recommendation_example()
    
    if basic_result and basic_result.get("recommendations"):
        diversity_recommendation_example()
        custom_user_history_example()
    else:
        logger.error("基本推荐示例失败，跳过其他示例")
    
    print("\n示例运行完成")