"""
应用内业务常量（非敏感）。

敏感连接串仍放在仓根 `.env` 的 `DATABASE_URL` 中。
"""

# 列表接口默认每页条数
DEFAULT_LIST_LIMIT: int = 100

# 列表接口单次请求允许的最大条数（防止大查询拖垮数据库）
MAX_LIST_LIMIT: int = 500
