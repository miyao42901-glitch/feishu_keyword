# 数据库与 ORM 约定

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`**（SQLAlchemy 模型、`DATABASE_URL`） |
| **相关文档** | [server 技术栈与文档索引](./server/README.md) · [HTTP 接口](./server/HTTP_API.md) · [工程约定](./DEVELOPMENT.md) |

本文档描述**逻辑库、连接配置、表与字段**；DDL 真源为 **`server/migrations/schema.sql`**，变更后请同步更新本文档与 `social_platform/models/`。

---

## 1. 逻辑库与服务配置

| 配置项 | 位置 | 说明 |
|--------|------|------|
| 逻辑库名 | MySQL | **`feishu_keyword`** |
| 连接串 | 仓根 `.env` | 变量 **`DATABASE_URL`** |
| 模板 | 仓根 `.env.example` / `.env.test` / `.env.master` | 占位可提交；真实口令在栈根 `.env`（gitignore） |

**`DATABASE_URL` 格式**（SQLAlchemy + PyMySQL）：

```text
mysql+pymysql://用户名:密码@主机:端口/feishu_keyword?charset=utf8mb4
```

- 密码中含 `@`、`#`、`%` 等字符时需做 **URL 编码**。
- **禁止**将含真实口令的 `.env` 提交到 Git。

**字符集**：库/表使用 **`utf8mb4`**，与连接串 `charset=utf8mb4` 一致。

**建表**：新库由 `api` 在 `DATABASE_RUN_MIGRATIONS=1` 时执行 `schema.sql`，再由 `db_migrate.py` 补丁；见 [server/migrations/README.md](../server/migrations/README.md)。

---

## 2. 代码与库表对应关系

| 用途 | 路径 |
|------|------|
| 会话 | `social_platform/database/session.py` |
| ORM 实体 | `social_platform/models/async_task.py`、`social_platform/models/results/*.py` |
| 迁移 | `social_platform/database/db_migrate.py` |

新增或变更列：**先改 `schema.sql` 与迁移脚本 → 再改本文档与 ORM**。

---

## 3. 表一览（共 5 张）

| 表名 | 说明 |
|------|------|
| `feishu_async_tasks` | 异步采集任务主表（状态、调度、Celery 关联） |
| `feishu_douyin_results` | 抖音搜索结果 |
| `feishu_xhs_results` | 小红书搜索结果 |
| `feishu_wxvideo_results` | 视频号搜索结果 |
| `feishu_mp_results` | 公众号文章搜索结果 |

各结果表通过 `task_id` 外键关联 `feishu_async_tasks.id`（`ON DELETE CASCADE`）。同步接口写入时 `task_id` 可为 `NULL`。

---

## 4. 字段说明

约定：`PK` 主键，`AI` 自增；时间字段在库中按 **UTC** 存储（应用层约定）。

### 4.1 `feishu_async_tasks`（异步任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint, PK, AI | 任务 ID |
| `user_id` | varchar(64) | 调用方用户 ID（与 YDDM `users/me` 的 `data.id` 一致） |
| `task_name` | varchar(100) | 任务名称（1～100 字符） |
| `status` | varchar(32) | `pending` / `running` / `success` / `failed` / `cancelled` |
| `action` | varchar(128) | 对外 action（kebab-case），如 `douyin-search-all` |
| `body_json` | json | 请求 body（不含 API Key） |
| `api_key` | varchar(128) | 提交任务时的 API Key |
| `error_message` | varchar(64), NULL | 失败摘要 |
| `celery_task_id` | varchar(128), NULL | Celery `AsyncResult.id` |
| `priority` | int | 优先级 0–9，越大越高 |
| `cancel_requested` | tinyint(1) | 是否已请求取消 |
| `success_count` | int | 落库成功条数累计 |
| `failed_count` | int | 落库失败/跳过条数累计 |
| `task_start_time` | datetime | 定时开始（前端传入，UTC） |
| `task_end_time` | datetime | 定时结束（前端传入，UTC） |
| `next_run_at` | datetime, NULL | 下次调度时间；`running` 时为 NULL |
| `current_run_id` | varchar(64), NULL | 当前执行轮次 UUID |
| `running_lease_until` | datetime, NULL | `running` 租约到期 |
| `interval_minutes` | int | 采集频率（分钟），最小 5，默认 60 |
| `fetch_count` | int | 单次采集上限 1～500，默认 100 |
| `create_time` | datetime | 创建时间 |
| `update_time` | datetime | 更新时间 |

索引：`status`、`user_id`、`action`、`celery_task_id`；组合 `(user_id, status, id DESC)`。

### 4.2 `feishu_douyin_results` / `feishu_xhs_results`（抖音 / 小红书）

两表列结构一致（小红书多 `xsec_token`）。主要字段：

| 字段 | 说明 |
|------|------|
| `id` | 自增主键 |
| `task_id` | 关联任务，同步可为 NULL |
| `user_id` | 用户 ID |
| `post_id` | 平台内容主键（抖音 `aweme_id` / 小红书 `note_id`），**唯一** |
| `keyword` | 搜索关键词 |
| `nickname` | 作者昵称 |
| `sec_uid` | 作者平台 ID |
| `content_type` | 内容类型 |
| `is_upload` | 是否已上传（外部系统更新） |
| `title` | 标题 |
| `summary` | 正文摘要（TEXT，应用写入） |
| `page_url` | 详情页链接 |
| `xsec_token` | 仅小红书：笔记 token |
| `avatar_url` | 头像 |
| `author_signature` | 签名 |
| `verify_name` | 认证文案 |
| `cover_url` | 封面 |
| `duration_seconds` | 视频时长（秒） |
| `has_music` | 是否含音乐 |
| `publish_time_ms` | 发布时间毫秒时间戳 |
| `like_count` / `comment_count` / `share_count` / `collect_count` | 互动数 |
| `primary_image_url` / `primary_video_url` | 主图 / 主视频地址 |
| `create_time` / `update_time` | 入库与更新时间 |

### 4.3 `feishu_wxvideo_results`（视频号）

| 字段 | 说明 |
|------|------|
| `post_id` | 视频 `exportId`，**唯一** |
| `keyword` | 搜索关键词 |
| `nickname` / `avatar_url` | UP 主信息 |
| `title` | 标题 |
| `publish_time` | 发布时间（毫秒时间戳） |
| `duration` | 时长（秒） |
| `cover_url` / `video_url` | 封面与下载链接 |
| `like_count` / `comment_count` / `forward_count` / `thumb_count` | 互动数 |
| `is_upload` | 是否已上传 |
| `task_id` / `user_id` | 任务与用户 |

### 4.4 `feishu_mp_results`（公众号）

| 字段 | 说明 |
|------|------|
| `post_id` | 文章 ID，**唯一** |
| `keyword` | 搜索关键词 |
| `company_name` | 公众号名称 |
| `biz` | 公众号 `biz` |
| `title` / `summary` | 标题与摘要 |
| `url` | 文章链接 |
| `avatar_url` | 作者头像 |
| `publish_time` | 发布时间（毫秒时间戳） |
| `is_upload` | 是否已上传 |
| `task_id` / `user_id` | 任务与用户 |

---

## 5. 查询与事务（开发约定）

- 复杂查询放在 **`social_platform/services/`**，路由层调用服务函数。
- 需要事务时在服务层同一 `Session` 内 `commit`/`rollback`。

---

## 6. 变更检查清单

1. 更新 **`server/migrations/schema.sql`**（及必要的增量 SQL）。
2. 更新 **本文档** 对应表节。
3. 更新 **`social_platform/models/`**。
4. 若有对外 API 字段变更，同步 **`docs/server/HTTP_API.md`** 与 `schemas`。
