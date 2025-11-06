"""
FastAPI 服务端
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import logging
from datetime import datetime

from ..services import DatabaseService, DataFetcher, SchedulerService
from ..tools import StockTools, get_stock_tools_definitions
from ..config import config
from .llm_handler import LLMHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="A股数据分析API",
    description="提供A股股票数据查询和LLM对话服务",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
db_service = None
scheduler_service = None
stock_tools = None
llm_handler = None


# Pydantic 模型
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False


class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls: Optional[List[Dict]] = None


class UpdateRequest(BaseModel):
    update_type: str  # "all" or "daily"
    stock_codes: Optional[List[str]] = None


class StockListRequest(BaseModel):
    """股票列表查询请求"""
    page: int = 1
    page_size: int = 50
    keyword: Optional[str] = None
    industry: Optional[str] = None
    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    min_pb: Optional[float] = None
    max_pb: Optional[float] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    min_turnover: Optional[float] = None
    max_turnover: Optional[float] = None
    sort_by: Optional[str] = "code"  # code, pe_ratio, pb_ratio, market_cap, turnover_rate
    sort_order: Optional[str] = "asc"  # asc, desc


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global db_service, scheduler_service, stock_tools, llm_handler

    logger.info("正在初始化服务...")

    # 初始化数据库服务
    db_service = DatabaseService()

    # 初始化调度器
    scheduler_service = SchedulerService(db_service)
    scheduler_service.start(run_immediately=False)

    # 初始化股票工具
    stock_tools = StockTools(db_service)

    # 初始化 LLM 处理器
    llm_handler = LLMHandler(stock_tools)

    logger.info("服务初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    global scheduler_service

    if scheduler_service:
        scheduler_service.stop()

    logger.info("服务已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A股数据分析API服务",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/api/stats")
async def get_stats():
    """获取数据库统计信息"""
    try:
        stock_count = db_service.get_stock_count()
        daily_count = db_service.get_daily_data_count()
        latest_date = db_service.get_latest_trade_date()

        return {
            "success": True,
            "data": {
                "total_stocks": stock_count,
                "total_daily_records": daily_count,
                "latest_trade_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/search")
async def search_stocks(keyword: str, limit: int = 20):
    """搜索股票"""
    try:
        stocks = db_service.search_stocks(keyword, limit)

        data = []
        for stock in stocks:
            data.append({
                "code": stock.code,
                "name": stock.name,
                "market": stock.market,
                "industry": stock.industry,
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "market_cap": stock.total_market_cap,
                "turnover_rate": stock.turnover_rate
            })

        return {"success": True, "data": data, "count": len(data)}

    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{stock_code}")
async def get_stock_detail(stock_code: str):
    """获取股票详情"""
    try:
        stock = db_service.get_stock_by_code(stock_code)

        if not stock:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code}")

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

        return {"success": True, "data": data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{stock_code}/history")
async def get_stock_history(stock_code: str, days: int = 30):
    """获取股票历史数据"""
    try:
        from datetime import timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        history = db_service.get_stock_daily_history(
            stock_code, start_date=start_date, end_date=end_date, limit=days
        )

        if not history:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的历史数据")

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

        return {"success": True, "data": data, "count": len(data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update")
async def trigger_update(request: UpdateRequest, background_tasks: BackgroundTasks):
    """触发数据更新"""
    try:
        if request.update_type == "all":
            background_tasks.add_task(scheduler_service.update_all_stocks)
            return {"success": True, "message": "已开始更新所有股票基本信息"}
        elif request.update_type == "daily":
            background_tasks.add_task(
                scheduler_service.update_daily_data,
                request.stock_codes
            )
            return {"success": True, "message": "已开始更新每日数据"}
        else:
            raise HTTPException(status_code=400, detail="无效的更新类型")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def get_tools():
    """获取可用的工具定义"""
    return {
        "success": True,
        "tools": get_stock_tools_definitions()
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    与 LLM 对话接口，支持 Function Calling

    支持的消息格式:
    {
        "messages": [
            {"role": "user", "content": "帮我查询平安银行的股票信息"}
        ],
        "stream": false
    }
    """
    try:
        if not llm_handler:
            raise HTTPException(status_code=503, detail="LLM服务未初始化")

        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 调用 LLM
        response = llm_handler.chat(messages)

        return {
            "success": True,
            "message": {
                "role": "assistant",
                "content": response.get("content", "")
            },
            "tool_calls": response.get("tool_calls")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stocks/list")
async def get_stock_list(request: StockListRequest):
    """
    获取股票列表（支持过滤、排序、分页）
    """
    try:
        from sqlalchemy import or_, and_, desc, asc
        from ..models import Stock

        session = db_service.get_session()

        try:
            # 构建查询
            query = session.query(Stock)

            # 关键词搜索
            if request.keyword:
                query = query.filter(
                    or_(
                        Stock.code.like(f"%{request.keyword}%"),
                        Stock.name.like(f"%{request.keyword}%")
                    )
                )

            # 行业筛选
            if request.industry:
                query = query.filter(Stock.industry.like(f"%{request.industry}%"))

            # 市盈率筛选
            if request.min_pe is not None:
                query = query.filter(Stock.pe_ratio >= request.min_pe)
            if request.max_pe is not None:
                query = query.filter(Stock.pe_ratio <= request.max_pe)

            # 市净率筛选
            if request.min_pb is not None:
                query = query.filter(Stock.pb_ratio >= request.min_pb)
            if request.max_pb is not None:
                query = query.filter(Stock.pb_ratio <= request.max_pb)

            # 市值筛选
            if request.min_market_cap is not None:
                query = query.filter(Stock.total_market_cap >= request.min_market_cap)
            if request.max_market_cap is not None:
                query = query.filter(Stock.total_market_cap <= request.max_market_cap)

            # 换手率筛选
            if request.min_turnover is not None:
                query = query.filter(Stock.turnover_rate >= request.min_turnover)
            if request.max_turnover is not None:
                query = query.filter(Stock.turnover_rate <= request.max_turnover)

            # 总数
            total = query.count()

            # 排序
            sort_field = getattr(Stock, request.sort_by, Stock.code)
            if request.sort_order == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))

            # 分页
            offset = (request.page - 1) * request.page_size
            stocks = query.offset(offset).limit(request.page_size).all()

            # 格式化数据
            data = []
            for stock in stocks:
                data.append({
                    "code": stock.code,
                    "name": stock.name,
                    "market": stock.market,
                    "industry": stock.industry,
                    "pe_ratio": stock.pe_ratio,
                    "pb_ratio": stock.pb_ratio,
                    "roe": stock.roe,
                    "total_market_cap": stock.total_market_cap,
                    "circulating_market_cap": stock.circulating_market_cap,
                    "turnover_rate": stock.turnover_rate,
                    "updated_at": stock.updated_at.strftime("%Y-%m-%d %H:%M:%S") if stock.updated_at else None
                })

            return {
                "success": True,
                "data": data,
                "pagination": {
                    "page": request.page,
                    "page_size": request.page_size,
                    "total": total,
                    "total_pages": (total + request.page_size - 1) // request.page_size
                }
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/industries")
async def get_industries():
    """获取所有行业列表"""
    try:
        from sqlalchemy import func
        from ..models import Stock

        session = db_service.get_session()

        try:
            # 查询所有不同的行业
            industries = session.query(
                Stock.industry,
                func.count(Stock.code).label('count')
            ).filter(
                Stock.industry.isnot(None)
            ).group_by(
                Stock.industry
            ).order_by(
                func.count(Stock.code).desc()
            ).all()

            data = [
                {"industry": ind, "count": count}
                for ind, count in industries
                if ind
            ]

            return {"success": True, "data": data}

        finally:
            session.close()

    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{stock_code}/kline")
async def get_stock_kline(stock_code: str, days: int = 90):
    """
    获取股票K线数据（用于绘图）
    返回格式适合 ECharts K线图
    """
    try:
        from datetime import timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        history = db_service.get_stock_daily_history(
            stock_code, start_date=start_date, end_date=end_date, limit=days * 2
        )

        if not history:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的K线数据")

        # 格式化为K线图需要的数据格式
        dates = []
        kline_data = []
        volume_data = []

        # 按日期升序排序
        history_sorted = sorted(history, key=lambda x: x.trade_date)

        for record in history_sorted:
            dates.append(record.trade_date.strftime("%Y-%m-%d"))
            # K线数据 [开盘价, 收盘价, 最低价, 最高价]
            kline_data.append([
                float(record.open) if record.open else 0,
                float(record.close) if record.close else 0,
                float(record.low) if record.low else 0,
                float(record.high) if record.high else 0
            ])
            # 成交量
            volume_data.append(int(record.volume) if record.volume else 0)

        return {
            "success": True,
            "data": {
                "dates": dates,
                "kline": kline_data,
                "volume": volume_data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = None, port: int = None, reload: bool = False):
    """启动服务器"""
    host = host or config.api.host
    port = port or config.api.port

    logger.info(f"正在启动服务器: http://{host}:{port}")

    uvicorn.run(
        "stock_analyzer.api.server:app",
        host=host,
        port=port,
        reload=reload
    )
