"""
领域模型包：ORM 实体导出。

- `Base`：所有表模型的基类；
- 其余类与 MySQL 中同名表映射，供 `app.services` 与（必要时）路由直接使用。
"""

from app.models.base import Base
from app.models.tables import (
    AiSummary,
    AlertRecord,
    Collection,
    CompetitorComparison,
    CrawledData,
    CrawlTask,
    DataExport,
    Feedback,
    FeishuSyncLog,
    FeishuTaskConfig,
    FilterRule,
    KeywordVersion,
    MonitoringLog,
    MonitoringPlan,
    MultimediaRecord,
    PropagationPath,
    Report,
    SentimentAnalysis,
    SourceConfig,
    TargetedMonitor,
    ThresholdRule,
    UserView,
)

__all__ = [
    "Base",
    "AiSummary",
    "AlertRecord",
    "Collection",
    "CompetitorComparison",
    "CrawledData",
    "CrawlTask",
    "DataExport",
    "Feedback",
    "FeishuSyncLog",
    "FeishuTaskConfig",
    "FilterRule",
    "KeywordVersion",
    "MonitoringLog",
    "MonitoringPlan",
    "MultimediaRecord",
    "PropagationPath",
    "Report",
    "SentimentAnalysis",
    "SourceConfig",
    "TargetedMonitor",
    "ThresholdRule",
    "UserView",
]
