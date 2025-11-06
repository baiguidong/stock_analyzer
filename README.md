# A股数据分析系统

一个功能完整的A股股票数据分析系统，支持数据获取、存储、查询，并集成大模型（LLM）进行智能分析。

## ✨ 主要特性

- 📊 **数据获取**: 使用 akshare 获取A股实时和历史数据
- 💾 **数据存储**: 支持 SQLite、MySQL、PostgreSQL 等多种数据库
- 🔄 **自动更新**: 定时自动更新股票数据
- 🤖 **LLM 集成**: 支持 OpenAI、Anthropic Claude、Ollama 等多种大模型
- 🛠️ **Function Calling**: 大模型可直接调用股票查询工具
- 🖥️ **多种接口**:
  - CLI 命令行工具
  - REST API 服务
  - Web 可视化界面（多标签页）
- 🎨 **Web 功能**:
  - AI 对话：与大模型智能交互
  - 股票列表：支持过滤、排序、分页
  - 股票详情：K线图、成交量图、财务指标
- 🎯 **灵活部署**: Client/Server 架构，支持分布式部署

## 📦 安装

### 1. 克隆或下载项目

```bash
cd /data/stock
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化配置

```bash
# 复制配置文件模板
cp config.yaml.example config.yaml

# 或使用 CLI 工具
python cli.py init-config
```

### 4. 编辑配置文件

编辑 `config.yaml`，填入必要信息：

```yaml
# 数据库配置（默认使用 SQLite，无需额外配置）
database:
  url: "sqlite:///./stock_data.db"

# 大模型配置（必须配置）
llm:
  provider: "openai"  # 或 anthropic, ollama
  api_key: "your-api-key-here"  # 填入你的 API Key
  model: "gpt-4-turbo-preview"
```

## 🚀 快速开始

### 方式一：服务端模式（推荐）

启动服务端，提供 API 和自动更新功能：

```bash
python cli.py server
```

服务启动后：
- API 文档: http://localhost:8000/docs
- Web 界面: 在浏览器打开 `stock_analyzer/web/index.html`

### 方式二：客户端模式

启动交互式命令行对话：

```bash
python cli.py client
```

### 方式三：直接使用 CLI 命令

```bash
# 查看帮助
python cli.py --help

# 手动更新数据
python cli.py update all  # 更新所有数据
python cli.py update stocks  # 仅更新股票信息
python cli.py update daily  # 仅更新每日数据

# 查看统计
python cli.py stats

# 搜索股票
python cli.py search 平安
```

## 📖 使用说明

### CLI 命令

```bash
# 启动服务端
python cli.py server [--host HOST] [--port PORT] [--reload]

# 启动客户端对话
python cli.py client

# 手动更新数据
python cli.py update <all|stocks|daily> [--codes CODE1,CODE2,...]

# 查看数据库统计
python cli.py stats

# 搜索股票
python cli.py search <关键词>

# 初始化配置文件
python cli.py init-config
```

### API 接口

启动服务端后，可通过 REST API 访问：

```bash
# 获取统计信息
GET http://localhost:8000/api/stats

# 获取股票列表（支持过滤、排序、分页）
POST http://localhost:8000/api/stocks/list
Content-Type: application/json

{
  "page": 1,
  "page_size": 50,
  "keyword": "平安",
  "industry": "银行",
  "min_pe": 5,
  "max_pe": 15,
  "sort_by": "pe_ratio",
  "sort_order": "asc"
}

# 获取行业列表
GET http://localhost:8000/api/industries

# 获取K线数据
GET http://localhost:8000/api/stocks/600000/kline?days=90

# 搜索股票
GET http://localhost:8000/api/stocks/search?keyword=平安&limit=20

# 获取股票详情
GET http://localhost:8000/api/stocks/600000

# 获取历史数据
GET http://localhost:8000/api/stocks/600000/history?days=30

# 与 LLM 对话
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "查询平安银行的股票信息"}
  ]
}

# 触发数据更新
POST http://localhost:8000/api/update
Content-Type: application/json

{
  "update_type": "all"
}
```

### Web 界面

启动服务端后，在浏览器中打开 `stock_analyzer/web/index.html` 即可使用Web界面。

#### 功能标签页

**1. AI对话标签页**
- 与大模型进行智能对话
- 自然语言查询股票信息
- 支持示例问题快速查询
- 实时显示对话历史

**2. 股票列表标签页**
- 查看所有股票列表
- 支持多条件过滤：
  - 关键词搜索（代码/名称）
  - 行业筛选
  - 市盈率范围
  - 市值范围
- 支持排序：
  - 按股票代码
  - 按市盈率/市净率
  - 按市值
  - 按换手率
- 分页浏览，每页50条
- 点击股票代码可跳转到详情页

**3. 股票详情标签页**
- 输入股票代码查询详细信息
- 显示财务指标卡片：
  - 市盈率、市净率、ROE
  - 总市值、流通市值
  - 换手率
  - 总资产、净资产
- K线图展示（最近90天）：
  - 支持缩放和拖动
  - 蜡烛图显示价格走势
- 成交量柱状图
- 响应式设计，自适应屏幕

#### 使用示例

```bash
# 1. 启动服务端
python cli.py server

# 2. 打开浏览器访问
# 方式1: 直接打开文件
open stock_analyzer/web/index.html  # macOS
start stock_analyzer/web/index.html  # Windows
xdg-open stock_analyzer/web/index.html  # Linux

# 方式2: 或者在浏览器地址栏输入
file:///完整路径/stock_analyzer/web/index.html
```

#### 界面截图说明

- **顶部统计栏**: 显示股票总数、数据记录数、最新交易日期
- **标签页切换**: 点击标签页按钮切换不同功能
- **实时更新**: 统计信息每30秒自动刷新

## 🔧 配置说明

### 数据库配置

支持多种数据库：

```yaml
database:
  # SQLite (默认)
  url: "sqlite:///./stock_data.db"

  # MySQL
  # url: "mysql+pymysql://user:password@localhost:3306/stock_db"

  # PostgreSQL
  # url: "postgresql://user:password@localhost:5432/stock_db"
```

### 大模型配置

#### OpenAI

```yaml
llm:
  provider: "openai"
  api_key: "sk-xxx"
  base_url: "https://api.openai.com/v1"  # 可选
  model: "gpt-4-turbo-preview"
```

#### Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  api_key: "sk-ant-xxx"
  model: "claude-3-opus-20240229"
```

#### Ollama (本地)

```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  model: "llama2"
```

### 更新调度配置

```yaml
update_schedule:
  daily_update_time: "16:00"  # 每日更新时间
  auto_update: true  # 是否启用自动更新
  update_on_start: false  # 启动时是否立即更新
```

## 📊 数据模型

### 股票基本信息表 (stocks)

- 股票代码、名称、市场、行业
- 财务指标：净资产、市盈率、市净率、ROE
- 市场指标：总市值、流通市值、换手率

### 每日行情表 (stock_daily)

- 价格：开盘价、收盘价、最高价、最低价
- 成交：成交量、成交额
- 涨跌：涨跌额、涨跌幅
- 市值、换手率

## 🛠️ LLM 工具函数

系统为大模型提供以下工具函数（Function Calling）：

1. **search_stock**: 搜索股票（按代码或名称）
2. **get_stock_detail**: 获取股票详细信息
3. **get_stock_history**: 获取历史行情数据
4. **filter_stocks**: 根据条件筛选股票
5. **get_database_stats**: 获取数据库统计信息

## 🏗️ 项目结构

```
stock/
├── stock_analyzer/
│   ├── models/          # 数据库模型
│   │   └── stock.py
│   ├── services/        # 业务逻辑
│   │   ├── data_fetcher.py   # 数据获取
│   │   ├── database.py       # 数据库操作
│   │   └── scheduler.py      # 定时任务
│   ├── tools/           # LLM 工具定义
│   │   └── stock_tools.py
│   ├── api/             # API 服务
│   │   ├── server.py         # FastAPI 服务
│   │   └── llm_handler.py    # LLM 处理器
│   ├── web/             # Web 界面
│   │   └── index.html
│   └── config.py        # 配置管理
├── cli.py               # CLI 工具
├── config.yaml.example  # 配置模板
├── requirements.txt     # 依赖
└── README.md           # 文档
```

## 🔍 示例查询

### CLI 客户端对话

```
你: 查询平安银行的股票信息
🤖 助手: 平安银行（股票代码：000001）的详细信息如下：
- 市盈率：5.23
- 市净率：0.67
- 总市值：3245.67亿元
- 换手率：0.89%
...

你: 帮我找市盈率低于15、市值大于100亿的股票
🤖 助手: 根据您的条件，我找到了以下股票：
1. 中国银行 (601988) - 市盈率: 4.56, 市值: 12345亿
2. 工商银行 (601398) - 市盈率: 5.12, 市值: 23456亿
...
```

### Python API

```python
from stock_analyzer.services import DatabaseService
from stock_analyzer.tools import StockTools

# 初始化
db = DatabaseService()
tools = StockTools(db)

# 搜索股票
result = tools.search_stock("平安")
print(result)

# 获取股票详情
detail = tools.get_stock_detail("000001")
print(detail)

# 筛选股票
stocks = tools.filter_stocks(min_pe=5, max_pe=15, min_market_cap=100)
print(stocks)
```

## ⚠️ 注意事项

1. **API Key**: 使用前必须在 `config.yaml` 中配置有效的 LLM API Key
2. **数据更新**: 首次运行需要手动触发数据更新：`python cli.py update all`
3. **网络要求**: akshare 需要访问互联网获取数据
4. **数据频率**: 建议在交易日收盘后（16:00 后）更新数据
5. **存储空间**: SQLite 数据库文件可能达到数百 MB，请确保有足够空间

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [akshare](https://github.com/akfamily/akshare) - 数据源
- [FastAPI](https://fastapi.tiangolo.com/) - API 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM 框架

## 📞 联系方式

如有问题，请提交 Issue 或联系开发者。

---

**祝您使用愉快！** 🎉
