# 数据库与 ORM 约定

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`**（SQLAlchemy 模型、`DATABASE_URL` 配置） |
| **相关文档** | [server 技术栈与文档索引](./server/README.md) · [HTTP 接口规范](./API.md) · [工程约定](./DEVELOPMENT.md) |

本文档描述**逻辑库、连接配置、表与字段**；与线上一致时以 MySQL 实际结构为准，修改表后请同步更新本文档与 `server/app/models/`。

---

## 1. 逻辑库与服务配置

| 配置项 | 位置 | 说明 |
|--------|------|------|
| 逻辑库名 | MySQL | **`feishu_keyword`**（创建库、建表、连接串中库名一致） |
| 连接串 | `server/.env` | 变量 **`DATABASE_URL`**，应用启动时由 `app.db` 读取 |
| 模板 | `server/.env.example` | 仅含占位符，**可提交**；真实密码写在 `.env` |

**`DATABASE_URL` 格式**（SQLAlchemy + PyMySQL）：

```text
mysql+pymysql://用户名:密码@主机:端口/feishu_keyword?charset=utf8mb4
```

示例（本机、空密码 root，仅供参考）：

```text
mysql+pymysql://root:@127.0.0.1:3306/feishu_keyword?charset=utf8mb4
```

- 密码中含 `@`、`#`、`%` 等字符时需做 **URL 编码**（如 `@` → `%40`）。
- **禁止**将 `server/.env` 提交到 Git；详见仓库根目录 `.gitignore`。

**字符集**：库/表建议使用 **`utf8mb4`**，与连接串 `charset=utf8mb4` 一致。

---

## 2. 代码与库表对应关系

| 用途 | 路径 |
|------|------|
| 引擎与会话 | `server/app/db.py`（`DATABASE_URL`、`engine`、`SessionLocal`、`check_database`） |
| 请求内会话注入 | `server/app/api/deps.py`（`get_db`） |
| ORM 实体 | `server/app/models/tables.py`（表名、列与下列结构对齐） |

新增或变更列：**先改 MySQL → 再改本文档与 `tables.py`**。

---

## 3. 表一览（当前共 21 张）

| 表名 | 说明 |
|------|------|
| `monitoring_plans` | 监控方案主数据 |
| `keyword_versions` | 关键词配置历史版本 |
| `source_configs` | 信源（含/排除）与抓取配置 |
| `crawl_tasks` | 采集任务调度与心跳、断点 |
| `crawled_data` | 采集结果明细 |
| `threshold_rules` | 互动量等阈值规则 |
| `targeted_monitors` | 定向监测（账号/话题/URL） |
| `feishu_sync_logs` | 飞书多维表格同步日志 |
| `alert_records` | 推送/告警记录与已读状态 |
| `ai_summaries` | AI 生成摘要与要点 |
| `collections` | 收藏/素材库（文件夹、标签、备注） |
| `competitor_comparisons` | 竞品声量与情感对比（按日） |
| `data_exports` | 导出任务（Excel/CSV/PDF/图片等） |
| `feedbacks` | 误报/不相关反馈 |
| `filter_rules` | 清洗与过滤规则 |
| `monitoring_logs` | 操作审计日志 |
| `multimedia_records` | 多媒体 OCR/ASR 解析结果 |
| `propagation_paths` | 传播路径溯源 |
| `reports` | 自动简报（日/周/月等） |
| `sentiment_analysis` | 情感分析结果 |
| `user_views` | 用户对告警/推送的阅读与浏览统计 |

---

## 4. 字段说明

约定：`PK` 主键，`AI` 自增；`NULL` 表示允许为空（以库表 `IS_NULLABLE` 为准）。**ENUM** 列出可选取值。

### 4.1 `monitoring_plans`（监控方案）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 方案 ID |
| `plan_name` | varchar(100) | 方案名称 |
| `status` | enum | `active` / `paused` / `expired` |
| `effective_time` | datetime | 生效时间 |
| `expire_time` | datetime | 过期时间 |
| `keyword_logic` | text | 关键词逻辑/配置文本 |
| `sync_word_expand` | tinyint(4) | 是否/开关类同义词扩展（0/1 等，以产品为准） |
| `version` | int | 当前配置版本号 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间（可带 ON UPDATE） |

### 4.2 `keyword_versions`（关键词版本）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联 `monitoring_plans.id` |
| `version_no` | int | 版本序号 |
| `keyword_config` | text | 该版本关键词配置（如 JSON/文本） |
| `created_by` | varchar(50) | 创建人标识 |
| `created_at` | timestamp | 创建时间 |

### 4.3 `source_configs`（信源配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `source_type` | enum | `website` / `wechat` / `weibo` / `douyin` / `feishu_doc` / `feishu_space` / `rss` |
| `source_url` | varchar(500) | 地址或标识 |
| `source_name` | varchar(200) | 展示名称 |
| `is_include` | tinyint(4) | 包含=1 / 排除=0（约定以产品为准） |
| `auth_config` | text | 认证等 JSON 文本 |
| `crawl_config` | text | 抓取参数 JSON 文本 |
| `status` | tinyint(4) | 启用等业务状态 |

### 4.4 `crawl_tasks`（采集任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `frequency` | int | 采集频率（如秒/分钟，与实现一致） |
| `last_crawl_time` | datetime | 上次采集时间 |
| `next_crawl_time` | datetime | 计划下次采集 |
| `last_checkpoint` | datetime | 断点/续传时间戳 |
| `status` | enum | `running` / `paused` / `stopped` |
| `heartbeat` | timestamp | 心跳 |
| `error_count` | int | 连续错误次数等 |

### 4.5 `crawled_data`（采集数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `source_type` | varchar(50) | 平台/类型 |
| `source_url` | varchar(500) | 原文链接 |
| `title` | text | 标题 |
| `content` | text | 正文或摘要 |
| `author` | varchar(100) | 作者 |
| `publish_time` | datetime | 发布时间 |
| `crawl_time` | datetime | 抓取时间 |
| `like_count` | int | 点赞数 |
| `comment_count` | int | 评论数 |
| `share_count` | int | 分享数 |
| `view_count` | int | 阅读/播放等 |
| `data_hash` | varchar(64) | 去重哈希 |
| `is_duplicate` | tinyint(4) | 是否重复标记 |

### 4.6 `threshold_rules`（阈值规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `rule_type` | enum | `like_count` / `comment_count` / `share_count` / `total_interaction` |
| `threshold_value` | int | 阈值 |
| `time_window` | int | 时间窗口（如分钟，与实现一致） |
| `alert_level` | enum | `low` / `medium` / `high` |

### 4.7 `targeted_monitors`（定向监测）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `monitor_type` | enum | `account` / `hashtag` / `url` |
| `target_value` | varchar(500) | 目标值（用户 ID、话题、URL 等） |
| `platform` | varchar(50) | 平台标识 |
| `is_active` | tinyint(4) | 是否启用 |

### 4.8 `feishu_sync_logs`（飞书多维同步日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `app_token` | varchar(100) | 飞书应用/多维应用 token |
| `table_id` | varchar(100) | 数据表 ID |
| `last_sync_time` | datetime | 最近同步时间 |
| `sync_status` | enum | `success` / `failed` / `syncing` |
| `record_count` | int | 本批同步条数 |
| `error_message` | text | 失败原因 |
| `created_at` | timestamp | 日志创建时间 |

### 4.9 `alert_records`（告警与推送记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联 `crawled_data.id`（或业务数据 ID） |
| `plan_id` | int | 关联方案 |
| `push_channel` | enum | `feishu_group` / `feishu_personal` |
| `push_time` | datetime | 推送时间 |
| `push_status` | enum | `success` / `failed` / `pending` |
| `webhook_url` | varchar(500) | 群机器人 Webhook（若适用） |
| `receiver_id` | varchar(100) | 接收人 open_id 等 |
| `is_read` | tinyint(4) | 是否已读 |
| `read_time` | datetime | 已读时间 |

### 4.10 `ai_summaries`（AI 摘要）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联 `crawled_data.id` |
| `summary` | text | 摘要正文 |
| `summary_length` | int | 摘要长度或目标长度（默认可 200） |
| `key_points` | text | 要点（如 JSON/列表文本） |
| `model_version` | varchar(50) | 模型版本标识 |
| `confidence_score` | decimal(3,2) | 置信度 |
| `generate_time` | datetime | 生成时间 |

### 4.11 `collections`（收藏/素材库）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联采集数据 |
| `plan_id` | int | 关联方案 |
| `user_id` | varchar(50) | 用户标识 |
| `folder_name` | varchar(100) | 文件夹名（库内默认可为「默认」等） |
| `tags` | varchar(500) | 标签 |
| `remark` | text | 备注 |
| `is_deleted` | tinyint(4) | 软删除标记 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### 4.12 `competitor_comparisons`（竞品对比）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `competitor_name` | varchar(100) | 竞品名称 |
| `competitor_keywords` | text | 竞品关键词配置 |
| `mention_count` | int | 提及次数 |
| `positive_count` | int | 正面条数 |
| `negative_count` | int | 负面条数 |
| `sentiment_score` | decimal(3,2) | 情感得分 |
| `comparison_date` | date | 统计日期 |
| `created_at` | timestamp | 创建时间 |

### 4.13 `data_exports`（数据导出）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `user_id` | varchar(50) | 发起人 |
| `export_type` | enum | `excel` / `csv` / `pdf` / `image` |
| `date_range_start` | datetime | 筛选开始 |
| `date_range_end` | datetime | 筛选结束 |
| `filter_criteria` | text | 筛选条件（如 JSON） |
| `file_url` | varchar(500) | 生成文件地址 |
| `file_size` | int | 文件大小 |
| `status` | enum | `pending` / `processing` / `completed` / `failed` |
| `error_message` | text | 失败原因 |
| `created_at` | timestamp | 创建时间 |
| `completed_at` | datetime | 完成时间 |

### 4.14 `feedbacks`（误报反馈）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联采集数据 |
| `plan_id` | int | 关联方案 |
| `user_id` | varchar(50) | 反馈人 |
| `feedback_type` | enum | `false_positive` / `false_negative` / `irrelevant` |
| `reason` | text | 原因说明 |
| `is_processed` | tinyint(4) | 是否已处理 |
| `processed_at` | datetime | 处理时间 |
| `created_at` | timestamp | 创建时间 |

### 4.15 `filter_rules`（过滤规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `rule_type` | enum | `exclude_keyword` / `min_interaction` / `max_age` / `min_length` / `spam_filter` |
| `rule_value` | text | 规则取值（如关键词、阈值 JSON） |
| `rule_description` | varchar(200) | 说明 |
| `priority` | int | 优先级 |
| `is_active` | tinyint(4) | 是否启用 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### 4.16 `monitoring_logs`（操作审计）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `user_id` | varchar(50) | 操作者 ID |
| `user_name` | varchar(100) | 操作者展示名 |
| `operation_type` | enum | `create` / `update` / `delete` / `export` / `pause` / `resume` / `rollback` / `config_change` |
| `target_type` | enum | `plan` / `keyword` / `source` / `rule` / `export` / `user` |
| `target_id` | int | 目标实体 ID |
| `plan_id` | int | 关联方案（若适用） |
| `operation_detail` | text | 详情（如 JSON） |
| `ip_address` | varchar(45) | IP |
| `user_agent` | text | UA |
| `created_at` | timestamp | 操作时间 |

### 4.17 `multimedia_records`（多媒体解析）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联采集数据 |
| `media_type` | enum | `image` / `video` / `audio` |
| `media_url` | varchar(500) | 媒体地址 |
| `ocr_text` | text | OCR 文本 |
| `asr_text` | text | 语音识别文本 |
| `recognized_keywords` | text | 命中关键词（如 JSON） |
| `process_time` | datetime | 处理时间 |

### 4.18 `propagation_paths`（传播路径）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联采集数据 |
| `root_source` | varchar(500) | 首发来源 |
| `root_author` | varchar(100) | 首发作者 |
| `root_time` | datetime | 首发时间 |
| `propagation_depth` | int | 传播层级深度 |
| `key_nodes` | text | 关键节点（如 JSON） |
| `propagation_chain` | text | 传播链 |
| `analysis_time` | datetime | 分析时间 |

### 4.19 `reports`（简报）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `plan_id` | int | 关联方案 |
| `report_type` | enum | `daily` / `weekly` / `monthly` / `custom` |
| `report_date` | date | 报告日期 |
| `report_title` | varchar(200) | 标题 |
| `report_content` | longtext | 正文（富文本/HTML 等） |
| `summary` | text | 摘要 |
| `total_count` | int | 总量 |
| `positive_count` | int | 正面量 |
| `negative_count` | int | 负面量 |
| `top_keywords` | text | 热词（如 JSON） |
| `file_url` | varchar(500) | 导出文件地址 |
| `send_status` | enum | `pending` / `sent` / `failed` |
| `send_time` | datetime | 发送时间 |
| `recipients` | text | 接收人列表（如 JSON） |
| `created_at` | timestamp | 创建时间 |

### 4.20 `sentiment_analysis`（情感分析）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `data_id` | int | 关联采集数据 |
| `plan_id` | int | 关联方案 |
| `sentiment` | enum | `positive` / `neutral` / `negative` |
| `confidence_score` | decimal(3,2) | 置信度 |
| `positive_keywords` | text | 正面触发词 |
| `negative_keywords` | text | 负面触发词 |
| `analyze_time` | datetime | 分析时间 |

### 4.21 `user_views`（用户阅读态）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int, PK, AI | 主键 |
| `alert_id` | int | 关联 `alert_records.id` |
| `user_id` | varchar(50) | 用户标识 |
| `is_read` | tinyint(4) | 是否已读 |
| `read_time` | datetime | 已读时间 |
| `view_count` | int | 浏览次数 |
| `first_view_time` | datetime | 首次打开时间 |
| `last_view_time` | datetime | 最近打开时间 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

---

## 5. 查询与事务（开发约定）

- 复杂查询放在 **`app/services/`**，路由通过 **`Depends(get_db)`** 注入 `Session`。
- 需要事务时在服务层同一 `Session` 内 `commit`/`rollback`，避免路由层散落提交逻辑。

---

## 6. 健康检查

- `check_database()`（`app.db`）仅执行连通性探测（如 `SELECT 1`），**不**承载业务查询。

---

## 7. 变更检查清单

1. 在 MySQL（phpMyAdmin / 迁移脚本）中完成 DDL。  
2. 更新 **本文档** 对应表节。  
3. 更新 **`server/app/models/tables.py`**。  
4. 若有对外 API 字段变更，同步 **`docs/API.md`** 与 Pydantic `schemas`。
