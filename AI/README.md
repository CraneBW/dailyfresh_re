# 生鲜购物网站推荐系统

一个基于用户历史购买行为的生鲜产品推荐系统，帮助用户发现符合个人口味和偏好的新鲜好物。

## 功能特点

- 基于用户历史购买数据生成个性化推荐
- 多级排序系统确保推荐质量（粗排序、精排序）
- 多样性优化算法提供多元化的推荐结果
- 提供详细的推荐解释，帮助用户理解推荐原因
- 缓存机制提高系统性能
- 支持不同环境配置（开发、生产、测试）

## 系统架构

系统由以下核心模块组成：

1. **推荐系统核心 (recommendation_system.py)**：负责生成和处理推荐
2. **排序引擎 (ranking.py)**：实现多级排序算法
3. **解释生成器 (explainability.py)**：为推荐结果生成可理解的解释
4. **配置管理 (config.py)**：管理不同环境的系统配置
5. **工具类 (utils.py)**：提供通用功能支持

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```


### 配置环境变量

创建 `.env` 文件并设置以下变量：

```plaintext
APP_ENV=development  # 可选：development, production, testing
```

### 使用示例

```python
from recommendation_system import get_recommendations

# 获取推荐
result = get_recommendations('user_history.json')

# 输出推荐结果
for item in result["recommendations"]:
    print(f"推荐产品: {item['recommendation']['product_name']}")
    print(f"类别: {item['recommendation']['category']}")
    print(f"价格: {item['recommendation']['price']}元")
    print(f"推荐理由: {' '.join(item['reasons'])}")
    print("---")
```

更多示例请参考 [example.py](file:///home/crane/文档/软件设计推荐系统插件/example.py)。

## 测试

运行单元测试：

```bash
python -m unittest tests.py
```

## 数据格式

### 用户历史数据格式

```json
{
  "user_id": "user123",
  "history_products": [
    {
      "product_name": "有机苹果",
      "timestamp": "2024-01-10",
      "category": "水果",
      "product_type": "新鲜水果",
      "price": 15.0,
      "rating": 9.0
    }
  ]
}
```

### 推荐结果格式

```json
{
  "recommendations": [
    {
      "recommendation": {
        "product_name": "有机蔬菜礼盒",
        "category": "蔬菜",
        "product_type": "礼盒装",
        "price": 50.0
      },
      "reasons": [
        "尝试新的蔬菜类型产品，扩展您的购物体验",
        "探索蔬菜类别，发现更多新鲜好物"
      ]
    }
  ],
  "evaluation_score": 8.5,
  "total_count": 1
}
```

## 扩展与定制

系统设计支持多种扩展方式：

1. 添加新的排序算法：扩展 [ranking.py](file:///home/crane/文档/软件设计推荐系统插件/ranking.py) 中的排序类
2. 自定义解释生成：修改 [explainability.py](file:///home/crane/文档/软件设计推荐系统插件/explainability.py) 中的模板和规则
3. 整合不同的数据源：通过修改 [load_user_history](file:///home/crane/文档/软件设计推荐系统插件/recommendation_system.py#L93-L145) 函数支持更多数据格式

## 许可证

MIT


