"""
股票查询工具定义 - 用于 LLM Function Calling
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy import text

from ..services.database import DatabaseService


class StockTools:
    """股票查询工具类"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def search_stock(self, keyword: str, limit: int = 10) -> str:
        """
        搜索股票

        Args:
            keyword: 股票代码或名称关键词
            limit: 返回结果数量限制

        Returns:
            JSON格式的股票列表
        """
        stocks = self.db_service.search_stocks(keyword, limit)

        if not stocks:
            return json.dumps({"success": False, "message": f"未找到包含 '{keyword}' 的股票"}, ensure_ascii=False)

        result = []
        for stock in stocks:
            result.append({
                "code": stock.code,
                "name": stock.name,
                "market": stock.market,
                "industry": stock.industry,
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "market_cap": stock.total_market_cap,
                "turnover_rate": stock.turnover_rate
            })

        return json.dumps({"success": True, "data": result, "count": len(result)}, ensure_ascii=False)

    def get_stock_detail(self, stock_code: str) -> str:
        """
        获取股票详细信息

        Args:
            stock_code: 股票代码（如：600000, 000001）

        Returns:
            JSON格式的股票详细信息
        """
        stock = self.db_service.get_stock_by_code(stock_code)

        if not stock:
            return json.dumps({"success": False, "message": f"未找到股票代码 {stock_code}"}, ensure_ascii=False)

        data = {
            "code": stock.code,
            "name": stock.name,
            "market": stock.market,
            "industry": stock.industry,
            "list_date": stock.list_date.strftime("%Y-%m-%d") if stock.list_date else None,
            "pe_ratio": stock.pe_ratio,
            "pb_ratio": stock.pb_ratio,
            "roe": stock.roe,
            "total_market_cap": stock.total_market_cap,
            "circulating_market_cap": stock.circulating_market_cap,
            "turnover_rate": stock.turnover_rate,
            "total_assets": stock.total_assets,
            "net_assets": stock.net_assets,
            "updated_at": stock.updated_at.strftime("%Y-%m-%d %H:%M:%S") if stock.updated_at else None
        }

        return json.dumps({"success": True, "data": data}, ensure_ascii=False)

    def get_stock_history(self, stock_code: str, days: int = 30) -> str:
        """
        获取股票历史行情

        Args:
            stock_code: 股票代码
            days: 获取最近多少天的数据，默认30天

        Returns:
            JSON格式的历史行情数据
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        history = self.db_service.get_stock_daily_history(
            stock_code, start_date=start_date, end_date=end_date, limit=days
        )

        if not history:
            return json.dumps({
                "success": False,
                "message": f"未找到股票 {stock_code} 的历史数据"
            }, ensure_ascii=False)

        data = []
        for record in history:
            data.append({
                "date": record.trade_date.strftime("%Y-%m-%d"),
                "open": record.open,
                "close": record.close,
                "high": record.high,
                "low": record.low,
                "volume": record.volume,
                "amount": record.amount,
                "change": record.change,
                "pct_change": record.pct_change,
                "turnover_rate": record.turnover_rate
            })

        return json.dumps({
            "success": True,
            "data": data,
            "count": len(data),
            "stock_code": stock_code
        }, ensure_ascii=False)

    def filter_stocks(self,
                     min_pe: Optional[float] = None,
                     max_pe: Optional[float] = None,
                     min_pb: Optional[float] = None,
                     max_pb: Optional[float] = None,
                     min_market_cap: Optional[float] = None,
                     max_market_cap: Optional[float] = None,
                     industry: Optional[str] = None,
                     limit: int = 20) -> str:
        """
        根据条件筛选股票

        Args:
            min_pe: 最小市盈率
            max_pe: 最大市盈率
            min_pb: 最小市净率
            max_pb: 最大市净率
            min_market_cap: 最小市值(亿元)
            max_market_cap: 最大市值(亿元)
            industry: 行业关键词
            limit: 返回结果数量限制

        Returns:
            JSON格式的股票列表
        """
        stocks = self.db_service.get_stocks_by_criteria(
            min_pe=min_pe, max_pe=max_pe,
            min_pb=min_pb, max_pb=max_pb,
            min_market_cap=min_market_cap, max_market_cap=max_market_cap,
            industry=industry,
            limit=limit
        )

        if not stocks:
            return json.dumps({
                "success": False,
                "message": "未找到符合条件的股票"
            }, ensure_ascii=False)

        data = []
        for stock in stocks:
            data.append({
                "code": stock.code,
                "name": stock.name,
                "industry": stock.industry,
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "roe": stock.roe,
                "market_cap": stock.total_market_cap,
                "turnover_rate": stock.turnover_rate
            })

        return json.dumps({
            "success": True,
            "data": data,
            "count": len(data),
            "filters": {
                "min_pe": min_pe, "max_pe": max_pe,
                "min_pb": min_pb, "max_pb": max_pb,
                "min_market_cap": min_market_cap, "max_market_cap": max_market_cap,
                "industry": industry
            }
        }, ensure_ascii=False)

    def execute_sql_query(self, query: str, limit: int = 100) -> str:
        """
        执行SQL查询语句（仅支持SELECT查询）

        Args:
            query: SQL查询语句（仅支持SELECT，不支持INSERT/UPDATE/DELETE等修改操作）
            limit: 返回结果数量限制，默认100，最大500

        Returns:
            JSON格式的查询结果

        数据库表结构说明:

        1. stocks表 - 股票基本信息
           - code (String): 股票代码，如'600000'（主键）
           - name (String): 股票名称，如'浦发银行'
           - market (String): 市场，SH(上海)/SZ(深圳)
           - industry (String): 行业，如'银行'
           - list_date (Date): 上市日期，格式YYYY-MM-DD
           - total_assets (Float): 总资产，单位：亿元
           - net_assets (Float): 净资产，单位：亿元
           - pe_ratio (Float): 市盈率（动态）
           - pb_ratio (Float): 市净率
           - roe (Float): 净资产收益率，单位：%
           - total_market_cap (Float): 总市值，单位：亿元
           - circulating_market_cap (Float): 流通市值，单位：亿元
           - turnover_rate (Float): 换手率，单位：%
           - updated_at (DateTime): 更新时间

        2. stock_daily表 - 股票每日行情数据
           - id (Integer): 自增主键
           - code (String): 股票代码
           - trade_date (Date): 交易日期，格式YYYY-MM-DD
           - open (Float): 开盘价
           - close (Float): 收盘价
           - high (Float): 最高价
           - low (Float): 最低价
           - volume (BigInteger): 成交量，单位：股
           - amount (Float): 成交额，单位：元
           - change (Float): 涨跌额
           - pct_change (Float): 涨跌幅，单位：%
           - total_market_cap (Float): 总市值，单位：亿元
           - circulating_market_cap (Float): 流通市值，单位：亿元
           - turnover_rate (Float): 换手率，单位：%
           - created_at (DateTime): 创建时间

        3. users表 - 用户信息（仅查询，不要在SQL中显示密码）
           - id (Integer): 用户ID（主键）
           - username (String): 用户名
           - email (String): 邮箱
           - is_active (Boolean): 是否激活
           - is_admin (Boolean): 是否管理员
           - created_at (DateTime): 创建时间
           - updated_at (DateTime): 更新时间

        4. favorites表 - 用户自选股票
           - id (Integer): 自选ID（主键）
           - user_id (Integer): 用户ID（外键，关联users.id）
           - stock_code (String): 股票代码（关联stocks.code）
           - added_at (DateTime): 添加时间

        示例查询:
        - 查询市盈率低于20的股票: "SELECT code, name, pe_ratio FROM stocks WHERE pe_ratio < 20 AND pe_ratio > 0 ORDER BY pe_ratio LIMIT 10"
        - 查询某股票近30天涨跌幅: "SELECT trade_date, close, pct_change FROM stock_daily WHERE code = '600000' ORDER BY trade_date DESC LIMIT 30"
        - 查询银行业股票: "SELECT code, name, pe_ratio, pb_ratio FROM stocks WHERE industry LIKE '%银行%'"
        - 联表查询自选股详情: "SELECT s.code, s.name, s.pe_ratio, f.added_at FROM stocks s JOIN favorites f ON s.code = f.stock_code WHERE f.user_id = 1"
        """
        # 安全检查：只允许SELECT查询
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return json.dumps({
                "success": False,
                "message": "仅支持SELECT查询，不允许执行INSERT/UPDATE/DELETE等修改操作"
            }, ensure_ascii=False)

        # 限制结果数量
        limit = min(limit, 500)  # 最大500条

        # 如果查询中没有LIMIT，自动添加
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        session = self.db_service.get_session()

        try:
            # 执行查询
            result = session.execute(text(query))
            rows = result.fetchall()

            # 获取列名
            if rows:
                # 将结果转换为字典列表
                columns = result.keys()
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 处理日期时间类型
                        if isinstance(value, (datetime, type(None))):
                            row_dict[col] = value.strftime("%Y-%m-%d %H:%M:%S") if value else None
                        elif hasattr(value, 'strftime'):  # Date类型
                            row_dict[col] = value.strftime("%Y-%m-%d")
                        else:
                            row_dict[col] = value
                    data.append(row_dict)

                return json.dumps({
                    "success": True,
                    "data": data,
                    "count": len(data),
                    "query": query
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "success": True,
                    "data": [],
                    "count": 0,
                    "message": "查询成功，但没有找到匹配的数据",
                    "query": query
                }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "success": False,
                "message": f"SQL查询执行失败: {str(e)}",
                "query": query
            }, ensure_ascii=False)

        finally:
            session.close()

    def get_database_stats(self) -> str:
        """
        获取数据库统计信息

        Returns:
            JSON格式的统计信息
        """
        stock_count = self.db_service.get_stock_count()
        daily_count = self.db_service.get_daily_data_count()
        latest_date = self.db_service.get_latest_trade_date()

        data = {
            "total_stocks": stock_count,
            "total_daily_records": daily_count,
            "latest_trade_date": latest_date.strftime("%Y-%m-%d") if latest_date else None
        }

        return json.dumps({
            "success": True,
            "data": data
        }, ensure_ascii=False)


def get_stock_tools_definitions() -> List[Dict[str, Any]]:
    """
    获取 LLM Function Calling 工具定义（OpenAI格式）

    Returns:
        工具定义列表
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_stock",
                "description": "搜索股票，可以通过股票代码或名称关键词搜索",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "股票代码或名称关键词，例如：'600000' 或 '平安银行'"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制，默认10",
                            "default": 10
                        }
                    },
                    "required": ["keyword"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_detail",
                "description": "获取指定股票的详细信息，包括财务指标、市值等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "股票代码，例如：'600000', '000001'"
                        }
                    },
                    "required": ["stock_code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_history",
                "description": "获取股票的历史行情数据，包括价格、成交量等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "股票代码，例如：'600000'"
                        },
                        "days": {
                            "type": "integer",
                            "description": "获取最近多少天的数据，默认30天",
                            "default": 30
                        }
                    },
                    "required": ["stock_code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "filter_stocks",
                "description": "根据条件筛选股票，支持按市盈率、市净率、市值、行业等条件筛选",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_pe": {
                            "type": "number",
                            "description": "最小市盈率"
                        },
                        "max_pe": {
                            "type": "number",
                            "description": "最大市盈率"
                        },
                        "min_pb": {
                            "type": "number",
                            "description": "最小市净率"
                        },
                        "max_pb": {
                            "type": "number",
                            "description": "最大市净率"
                        },
                        "min_market_cap": {
                            "type": "number",
                            "description": "最小市值(亿元)"
                        },
                        "max_market_cap": {
                            "type": "number",
                            "description": "最大市值(亿元)"
                        },
                        "industry": {
                            "type": "string",
                            "description": "行业关键词"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制，默认20",
                            "default": 20
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_sql_query",
                "description": """执行自定义SQL查询（仅支持SELECT查询，用于复杂数据分析）。

数据库表结构:
1. stocks表 - 股票基本信息
   - code: 股票代码(主键), name: 名称, market: 市场(SH/SZ), industry: 行业
   - pe_ratio: 市盈率, pb_ratio: 市净率, roe: ROE(%)
   - total_market_cap: 总市值(亿元), circulating_market_cap: 流通市值(亿元)
   - turnover_rate: 换手率(%), total_assets: 总资产(亿元), net_assets: 净资产(亿元)

2. stock_daily表 - 每日行情
   - code: 股票代码, trade_date: 交易日期
   - open/close/high/low: 开盘/收盘/最高/最低价
   - volume: 成交量(股), amount: 成交额(元)
   - pct_change: 涨跌幅(%), turnover_rate: 换手率(%)

3. favorites表 - 用户自选
   - user_id: 用户ID, stock_code: 股票代码, added_at: 添加时间

示例查询:
- "SELECT code, name, pe_ratio FROM stocks WHERE pe_ratio < 20 ORDER BY pe_ratio LIMIT 10"
- "SELECT trade_date, close, pct_change FROM stock_daily WHERE code='600000' ORDER BY trade_date DESC LIMIT 30"
- "SELECT s.code, s.name, s.pe_ratio FROM stocks s JOIN favorites f ON s.code=f.stock_code WHERE f.user_id=1"

当其他工具无法满足需求时使用此工具进行复杂查询。""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL查询语句（仅支持SELECT，必须是有效的SQL语法）"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制，默认100，最大500",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_database_stats",
                "description": "获取数据库统计信息，包括股票总数、数据记录数、最新交易日期等",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
