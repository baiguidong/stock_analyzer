# 快速开始指南

## 🚀 5分钟快速上手

### 第一步：安装依赖

```bash
# 进入项目目录
cd /data/stock

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置系统

```bash
# 复制配置文件
cp config.yaml.example config.yaml

# 编辑配置文件
nano config.yaml  # 或使用其他编辑器
```

**必须配置的项目：**

```yaml
llm:
  provider: "openai"  # 选择你的大模型提供商
  api_key: "your-api-key-here"  # 填入你的API Key
  model: "gpt-4-turbo-preview"  # 选择模型
```

### 第三步：验证安装

```bash
python verify.py
```

如果所有检查都通过，继续下一步。

### 第四步：初始化数据

```bash
# 首次运行，更新所有股票数据
# 注意：这可能需要10-30分钟
python cli.py update all
```

### 第五步：选择启动方式

#### 方式A：服务端模式（推荐）

```bash
python cli.py server
```

启动后：
- API文档: http://localhost:8000/docs
- Web界面: 打开浏览器访问 `stock_analyzer/web/index.html`

#### 方式B：客户端模式

```bash
python cli.py client
```

在命令行中直接与AI助手对话。

#### 方式C：使用快速启动脚本

```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

## 💡 常用命令

```bash
# 查看帮助
python cli.py --help

# 更新数据
python cli.py update all        # 更新所有数据
python cli.py update stocks     # 仅更新股票信息
python cli.py update daily      # 仅更新每日数据

# 查看统计
python cli.py stats

# 搜索股票
python cli.py search 平安

# 启动服务
python cli.py server --port 8000

# 启动客户端
python cli.py client
```

## 🎯 使用示例

### 命令行对话

```
$ python cli.py client

你: 查询平安银行的股票信息
🤖 助手: 平安银行（000001）的详细信息如下：
- 市盈率：5.23
- 市净率：0.67
- 总市值：3245.67亿元
...

你: 帮我找市盈率低于15的银行股
🤖 助手: 找到以下银行股票：
1. 中国银行 (601988) - 市盈率: 4.56
2. 工商银行 (601398) - 市盈率: 5.12
...
```

### API 调用

```bash
# 搜索股票
curl http://localhost:8000/api/stocks/search?keyword=平安

# 获取股票详情
curl http://localhost:8000/api/stocks/000001

# 与AI对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "查询贵州茅台的信息"}
    ]
  }'
```

### Python 代码

```python
from stock_analyzer.services import DatabaseService
from stock_analyzer.tools import StockTools

# 初始化
db = DatabaseService()
tools = StockTools(db)

# 搜索股票
result = tools.search_stock("平安")
print(result)

# 筛选低估值股票
stocks = tools.filter_stocks(max_pe=15, min_market_cap=100)
print(stocks)
```

## ⚠️ 常见问题

### 1. 配置文件错误

**问题**: `config.yaml` 不存在或格式错误

**解决**:
```bash
python cli.py init-config
# 然后编辑 config.yaml
```

### 2. 依赖安装失败

**问题**: pip 安装依赖时出错

**解决**:
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 数据库连接错误

**问题**: SQLite 或其他数据库连接失败

**解决**:
- 检查 `config.yaml` 中的 `database.url`
- SQLite 默认配置：`sqlite:///./stock_data.db`
- 确保目录有写入权限

### 4. API Key 无效

**问题**: LLM 调用失败

**解决**:
- 检查 `config.yaml` 中的 `llm.api_key`
- 确认 API Key 有效且有余额
- 检查 `llm.provider` 和 `llm.model` 配置

### 5. 数据更新慢

**问题**: 更新数据时间过长

**解决**:
- 首次更新需要获取所有股票数据，耗时较长是正常的
- 建议在非交易时间更新
- 可以只更新指定股票：
  ```bash
  python cli.py update daily --codes=000001,600000
  ```

### 6. Web 界面无法连接

**问题**: 打开 Web 页面后无法与后端通信

**解决**:
- 确保服务端正在运行：`python cli.py server`
- 检查服务端地址是否正确（默认 http://localhost:8000）
- 检查浏览器控制台是否有 CORS 错误

## 📚 进阶配置

### 使用 MySQL 数据库

```yaml
database:
  url: "mysql+pymysql://user:password@localhost:3306/stock_db"
```

需要安装：`pip install pymysql`

### 使用 Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  api_key: "sk-ant-xxx"
  model: "claude-3-opus-20240229"
```

需要安装：`pip install anthropic`

### 配置自动更新

```yaml
update_schedule:
  daily_update_time: "16:00"  # 每日16:00更新
  auto_update: true            # 启用自动更新
  update_on_start: true        # 启动时立即更新
```

### 修改服务端口

```yaml
api:
  host: "0.0.0.0"
  port: 8080  # 修改为其他端口
```

或使用命令行参数：
```bash
python cli.py server --port 8080
```

## 🎓 下一步

- 查看完整文档：`README.md`
- 探索 API 文档：http://localhost:8000/docs
- 查看项目结构和代码注释
- 根据需求定制和扩展功能

---

**祝您使用愉快！** 🎉
