"""
数据库表与 ORM 模型的映射定义。

本文件中的类与 `feishu_keyword` 库内已有表名、字段类型保持一致，用于读写业务数据。
字段含义以产品/库表设计为准；此处类文档仅概括职责。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MonitoringPlan(Base):
    """监控方案主表：方案名称、生效/过期、状态及关键词相关配置摘要。"""

    __tablename__ = "monitoring_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_name: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(
        Enum("active", "paused", "expired", name="monitoring_plans_status"),
    )
    effective_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    keyword_logic: Mapped[Optional[str]] = mapped_column(Text)
    sync_word_expand: Mapped[Optional[int]] = mapped_column(Integer)
    version: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


class FeishuTaskConfig(Base):
    """飞书插件任务配置：整单 JSON 快照，供列表与编辑回显。"""

    __tablename__ = "feishu_task_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_name: Mapped[Optional[str]] = mapped_column(String(200))
    config_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


class KeywordVersion(Base):
    """关键词配置历史版本：支持按方案回溯与回滚。"""

    __tablename__ = "keyword_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    version_no: Mapped[Optional[int]] = mapped_column(Integer)
    keyword_config: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class SourceConfig(Base):
    """信源配置：网站/社媒/飞书文档等包含或排除规则及抓取相关 JSON 配置。"""

    __tablename__ = "source_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    source_type: Mapped[Optional[str]] = mapped_column(
        Enum(
            "website",
            "wechat",
            "weibo",
            "douyin",
            "feishu_doc",
            "feishu_space",
            "rss",
            name="source_configs_source_type",
        ),
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    source_name: Mapped[Optional[str]] = mapped_column(String(200))
    is_include: Mapped[Optional[int]] = mapped_column(Integer)
    auth_config: Mapped[Optional[str]] = mapped_column(Text)
    crawl_config: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[int]] = mapped_column(Integer)


class CrawlTask(Base):
    """采集任务状态：频率、下次执行时间、断点、心跳与错误计数。"""

    __tablename__ = "crawl_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    frequency: Mapped[Optional[int]] = mapped_column(Integer)
    last_crawl_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_crawl_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    last_checkpoint: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[Optional[str]] = mapped_column(
        Enum("running", "paused", "stopped", name="crawl_tasks_status"),
        index=True,
    )
    heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_count: Mapped[Optional[int]] = mapped_column(Integer)


class CrawledData(Base):
    """采集结果明细：正文、互动量、去重哈希等。"""

    __tablename__ = "crawled_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    title: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(100))
    publish_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    crawl_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer)
    share_count: Mapped[Optional[int]] = mapped_column(Integer)
    view_count: Mapped[Optional[int]] = mapped_column(Integer)
    data_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    is_duplicate: Mapped[Optional[int]] = mapped_column(Integer)


class ThresholdRule(Base):
    """阈值规则：按互动量与时间窗口触发不同级别预警。"""

    __tablename__ = "threshold_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    rule_type: Mapped[Optional[str]] = mapped_column(
        Enum(
            "like_count",
            "comment_count",
            "share_count",
            "total_interaction",
            name="threshold_rules_rule_type",
        ),
    )
    threshold_value: Mapped[Optional[int]] = mapped_column(Integer)
    time_window: Mapped[Optional[int]] = mapped_column(Integer)
    alert_level: Mapped[Optional[str]] = mapped_column(
        Enum("low", "medium", "high", name="threshold_rules_alert_level"),
    )


class TargetedMonitor(Base):
    """定向监测：账号、话题标签或 URL 等精确目标。"""

    __tablename__ = "targeted_monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    monitor_type: Mapped[Optional[str]] = mapped_column(
        Enum("account", "hashtag", "url", name="targeted_monitors_monitor_type"),
        index=True,
    )
    target_value: Mapped[Optional[str]] = mapped_column(String(500))
    platform: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[Optional[int]] = mapped_column(Integer)


class FeishuSyncLog(Base):
    """飞书多维表格同步日志：同步时间、状态、条数与错误信息。"""

    __tablename__ = "feishu_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    app_token: Mapped[Optional[str]] = mapped_column(String(100))
    table_id: Mapped[Optional[str]] = mapped_column(String(100))
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sync_status: Mapped[Optional[str]] = mapped_column(
        Enum("success", "failed", "syncing", name="feishu_sync_logs_sync_status"),
        index=True,
    )
    record_count: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class AlertRecord(Base):
    """预警推送记录：渠道、送达状态、Webhook、接收人及已读标记。"""

    __tablename__ = "alert_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    push_channel: Mapped[Optional[str]] = mapped_column(
        Enum("feishu_group", "feishu_personal", name="alert_records_push_channel"),
    )
    push_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    push_status: Mapped[Optional[str]] = mapped_column(
        Enum("success", "failed", "pending", name="alert_records_push_status"),
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    receiver_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_read: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    read_time: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AiSummary(Base):
    """AI 摘要：关联单条采集数据，存储摘要、要点与模型信息。"""

    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    summary: Mapped[str] = mapped_column(Text)
    summary_length: Mapped[Optional[int]] = mapped_column(Integer)
    key_points: Mapped[Optional[str]] = mapped_column(Text)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    generate_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)


class Collection(Base):
    """收藏/素材库：用户对方案下某条数据的收藏、文件夹、标签与备注。"""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    folder_name: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[str]] = mapped_column(String(500), index=True)
    remark: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


class CompetitorComparison(Base):
    """竞品声量对比：按日统计提及量与情感分布等。"""

    __tablename__ = "competitor_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    competitor_name: Mapped[str] = mapped_column(String(100), index=True)
    competitor_keywords: Mapped[Optional[str]] = mapped_column(Text)
    mention_count: Mapped[Optional[int]] = mapped_column(Integer)
    positive_count: Mapped[Optional[int]] = mapped_column(Integer)
    negative_count: Mapped[Optional[int]] = mapped_column(Integer)
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    comparison_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class DataExport(Base):
    """数据导出任务：格式、时间范围、文件地址与处理状态。"""

    __tablename__ = "data_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(50))
    export_type: Mapped[str] = mapped_column(
        Enum("excel", "csv", "pdf", "image", name="data_exports_export_type"),
    )
    date_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    filter_criteria: Mapped[Optional[str]] = mapped_column(Text)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(
        Enum("pending", "processing", "completed", "failed", name="data_exports_status"),
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Feedback(Base):
    """误报/反馈：用户对某条数据标记误报类型，供规则或模型优化。"""

    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    feedback_type: Mapped[str] = mapped_column(
        Enum("false_positive", "false_negative", "irrelevant", name="feedbacks_feedback_type"),
        index=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text)
    is_processed: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class FilterRule(Base):
    """清洗/过滤规则：排除词、互动量下限、时效、长度、反垃圾等。"""

    __tablename__ = "filter_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    rule_type: Mapped[str] = mapped_column(
        Enum(
            "exclude_keyword",
            "min_interaction",
            "max_age",
            "min_length",
            "spam_filter",
            name="filter_rules_rule_type",
        ),
    )
    rule_value: Mapped[str] = mapped_column(Text)
    rule_description: Mapped[Optional[str]] = mapped_column(String(200))
    priority: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


class MonitoringLog(Base):
    """操作审计日志：谁在何时对计划/关键词等做了何种操作。"""

    __tablename__ = "monitoring_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(100))
    operation_type: Mapped[str] = mapped_column(
        Enum(
            "create",
            "update",
            "delete",
            "export",
            "pause",
            "resume",
            "rollback",
            "config_change",
            name="monitoring_logs_operation_type",
        ),
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        Enum("plan", "keyword", "source", "rule", "export", "user", name="monitoring_logs_target_type"),
        index=True,
    )
    target_id: Mapped[Optional[int]] = mapped_column(Integer)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer)
    operation_detail: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True)


class MultimediaRecord(Base):
    """多媒体解析：图片 OCR、音视频 ASR 及命中关键词等。"""

    __tablename__ = "multimedia_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    media_type: Mapped[str] = mapped_column(
        Enum("image", "video", "audio", name="multimedia_records_media_type"),
        index=True,
    )
    media_url: Mapped[str] = mapped_column(String(500))
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    asr_text: Mapped[Optional[str]] = mapped_column(Text)
    recognized_keywords: Mapped[Optional[str]] = mapped_column(Text)
    process_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)


class PropagationPath(Base):
    """传播路径溯源：首发源、深度、关键节点与传播链（多为 JSON 文本）。"""

    __tablename__ = "propagation_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    root_source: Mapped[Optional[str]] = mapped_column(String(500))
    root_author: Mapped[Optional[str]] = mapped_column(String(100))
    root_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    propagation_depth: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    key_nodes: Mapped[Optional[str]] = mapped_column(Text)
    propagation_chain: Mapped[Optional[str]] = mapped_column(Text)
    analysis_time: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Report(Base):
    """自动简报：日/周/月报内容、统计数据与发送状态。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    report_type: Mapped[str] = mapped_column(
        Enum("daily", "weekly", "monthly", "custom", name="reports_report_type"),
        index=True,
    )
    report_date: Mapped[date] = mapped_column(Date)
    report_title: Mapped[Optional[str]] = mapped_column(String(200))
    report_content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    total_count: Mapped[Optional[int]] = mapped_column(Integer)
    positive_count: Mapped[Optional[int]] = mapped_column(Integer)
    negative_count: Mapped[Optional[int]] = mapped_column(Integer)
    top_keywords: Mapped[Optional[str]] = mapped_column(Text)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    send_status: Mapped[Optional[str]] = mapped_column(
        Enum("pending", "sent", "failed", name="reports_send_status"),
        index=True,
    )
    send_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    recipients: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class SentimentAnalysis(Base):
    """情感分析结果：正/中/负及置信度、关键词命中。"""

    __tablename__ = "sentiment_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    sentiment: Mapped[str] = mapped_column(
        Enum("positive", "neutral", "negative", name="sentiment_analysis_sentiment"),
        index=True,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    positive_keywords: Mapped[Optional[str]] = mapped_column(Text)
    negative_keywords: Mapped[Optional[str]] = mapped_column(Text)
    analyze_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)


class UserView(Base):
    """用户侧阅读态：针对某条告警/推送的多用户已读、浏览次数与时间。"""

    __tablename__ = "user_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    is_read: Mapped[Optional[int]] = mapped_column(Integer)
    read_time: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    view_count: Mapped[Optional[int]] = mapped_column(Integer)
    first_view_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_view_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
