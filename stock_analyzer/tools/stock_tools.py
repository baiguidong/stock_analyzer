"""
股票查询工具定义 - 用于 LLM Function Calling
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

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
