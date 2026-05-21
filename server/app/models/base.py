"""
ORM 声明式基类。

所有与 MySQL 表一一对应的模型类均继承 `Base`，便于 `metadata` 统一管理（如未来做迁移工具链）。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式映射基类，自身不对应具体数据表。"""

    pass
