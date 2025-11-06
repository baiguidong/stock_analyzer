// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 全局状态
let conversationHistory = [
    {
        role: "system",
        content: "你是一个专业的A股股票分析助手。你可以帮助用户查询股票信息、分析市场数据。当用户询问股票相关问题时，你应该使用提供的工具函数来获取准确的数据。回答要简洁明了，使用中文。"
    }
];

let currentPage = 1;
let totalPages = 1;
let industries = [];

// =============== 通用函数 ===============

// 切换标签页
function switchTab(tabName) {
    // 移除所有active类
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // 添加active类到当前标签
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');

    // 根据标签页执行特定操作
    if (tabName === 'list') {
        loadIndustries();
        loadStockList();
    }
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();

        if (data.success) {
            document.getElementById('stockCount').textContent = data.data.total_stocks || '-';
            document.getElementById('recordCount').textContent = data.data.total_daily_records || '-';
            document.getElementById('latestDate').textContent = data.data.latest_trade_date || '-';
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 格式化数字
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '-';
    return parseFloat(num).toFixed(decimals);
}

// =============== Chat 功能 ===============

// 添加消息到界面
function addMessage(role, content) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    const formattedContent = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formattedContent}</div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// 显示/隐藏加载动画
function showLoading() {
    const messagesDiv = document.getElementById('messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="loading-spinner"></div>
            思考中...
        </div>
    `;
    messagesDiv.appendChild(loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideLoading() {
    const loadingDiv = document.getElementById('loading-message');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    addMessage('user', message);
    input.value = '';

    conversationHistory.push({
        role: 'user',
        content: message
    });

    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: conversationHistory,
                stream: false
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success && data.message) {
            const assistantMessage = data.message.content;
            addMessage('assistant', assistantMessage);

            conversationHistory.push({
                role: 'assistant',
                content: assistantMessage
            });
        } else {
            addMessage('assistant', '抱歉，我无法处理你的请求。请稍后再试。');
        }
    } catch (error) {
        hideLoading();
        console.error('发送消息失败:', error);
        addMessage('assistant', '抱歉，连接服务器失败。请确保服务端正在运行。');
    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}

// 发送示例问题
function sendExample(text) {
    document.getElementById('messageInput').value = text;
    sendMessage();
}

// 处理Enter键
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// =============== 股票列表功能 ===============

// 加载行业列表
async function loadIndustries() {
    if (industries.length > 0) return; // 已加载过

    try {
        const response = await fetch(`${API_BASE_URL}/api/industries`);
        const data = await response.json();

        if (data.success) {
            industries = data.data;
            const select = document.getElementById('filterIndustry');

            industries.forEach(item => {
                const option = document.createElement('option');
                option.value = item.industry;
                option.textContent = `${item.industry} (${item.count})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载行业列表失败:', error);
    }
}

// 加载股票列表
async function loadStockList(page = 1) {
    const loading = document.getElementById('stockListLoading');
    const empty = document.getElementById('stockListEmpty');
    const table = document.getElementById('stockTable');
    const tbody = document.getElementById('stockTableBody');

    loading.style.display = 'flex';
    empty.style.display = 'none';
    table.style.display = 'none';

    // 获取过滤条件
    const filters = {
        page: page,
        page_size: 50,
        keyword: document.getElementById('filterKeyword').value.trim() || null,
        industry: document.getElementById('filterIndustry').value || null,
        min_pe: parseFloat(document.getElementById('filterMinPE').value) || null,
        max_pe: parseFloat(document.getElementById('filterMaxPE').value) || null,
        min_market_cap: parseFloat(document.getElementById('filterMinCap').value) || null,
        max_market_cap: parseFloat(document.getElementById('filterMaxCap').value) || null,
        sort_by: document.getElementById('sortField').value,
        sort_order: document.getElementById('sortOrder').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/stocks/list`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filters)
        });

        const data = await response.json();
        loading.style.display = 'none';

        if (data.success && data.data.length > 0) {
            tbody.innerHTML = '';
            data.data.forEach(stock => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td><span class="stock-code" onclick="viewStockDetail('${stock.code}')">${stock.code}</span></td>
                    <td>${stock.name}</td>
                    <td>${stock.industry || '-'}</td>
                    <td>${formatNumber(stock.pe_ratio)}</td>
                    <td>${formatNumber(stock.pb_ratio)}</td>
                    <td>${formatNumber(stock.roe)}</td>
                    <td>${formatNumber(stock.total_market_cap)}</td>
                    <td>${formatNumber(stock.turnover_rate)}</td>
                `;
            });

            table.style.display = 'table';

            // 更新分页信息
            currentPage = data.pagination.page;
            totalPages = data.pagination.total_pages;
            updatePagination();
        } else {
            empty.style.display = 'block';
        }
    } catch (error) {
        console.error('加载股票列表失败:', error);
        loading.style.display = 'none';
        empty.style.display = 'block';
    }
}

// 更新分页信息
function updatePagination() {
    document.getElementById('pageInfo').textContent = `第 ${currentPage} / ${totalPages} 页`;
    document.getElementById('prevBtn').disabled = currentPage <= 1;
    document.getElementById('nextBtn').disabled = currentPage >= totalPages;
}

// 上一页
function prevPage() {
    if (currentPage > 1) {
        loadStockList(currentPage - 1);
    }
}

// 下一页
function nextPage() {
    if (currentPage < totalPages) {
        loadStockList(currentPage + 1);
    }
}

// 重置过滤条件
function resetFilters() {
    document.getElementById('filterKeyword').value = '';
    document.getElementById('filterIndustry').value = '';
    document.getElementById('filterMinPE').value = '';
    document.getElementById('filterMaxPE').value = '';
    document.getElementById('filterMinCap').value = '';
    document.getElementById('filterMaxCap').value = '';
    document.getElementById('sortField').value = 'code';
    document.getElementById('sortOrder').value = 'asc';
    loadStockList(1);
}

// =============== 股票详情功能 ===============

// 查看股票详情（从列表跳转）
function viewStockDetail(code) {
    document.getElementById('detailStockCode').value = code;
    switchTab('detail');
    // 需要手动设置active标签
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab')[2].classList.add('active'); // 详情是第3个标签
    loadStockDetail();
}

// 加载股票详情
async function loadStockDetail() {
    const code = document.getElementById('detailStockCode').value.trim();
    const content = document.getElementById('detailContent');

    if (!code) {
        content.innerHTML = '<div class="empty">请输入股票代码查询</div>';
        return;
    }

    content.innerHTML = '<div class="loading"><div class="loading-spinner"></div>加载中...</div>';

    try {
        // 并行加载股票信息和K线数据
        const [detailResponse, klineResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/stocks/${code}`),
            fetch(`${API_BASE_URL}/api/stocks/${code}/kline?days=90`)
        ]);

        const detailData = await detailResponse.json();
        const klineData = await klineResponse.json();

        if (!detailData.success) {
            content.innerHTML = `<div class="error">未找到股票: ${code}</div>`;
            return;
        }

        const stock = detailData.data;

        // 渲染股票详情
        content.innerHTML = `
            <div class="stock-header">
                <div>
                    <span class="stock-title">${stock.name}</span>
                    <span class="stock-code-badge">${stock.code}</span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: #64748b;">更新时间</div>
                    <div style="font-size: 14px;">${stock.updated_at || '-'}</div>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">市场</div>
                    <div class="info-value">${stock.market || '-'}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">行业</div>
                    <div class="info-value">${stock.industry || '-'}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">市盈率(动态)</div>
                    <div class="info-value">${formatNumber(stock.pe_ratio)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">市净率</div>
                    <div class="info-value">${formatNumber(stock.pb_ratio)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">ROE(%)</div>
                    <div class="info-value">${formatNumber(stock.roe)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">总市值(亿元)</div>
                    <div class="info-value">${formatNumber(stock.total_market_cap)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">流通市值(亿元)</div>
                    <div class="info-value">${formatNumber(stock.circulating_market_cap)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">换手率(%)</div>
                    <div class="info-value">${formatNumber(stock.turnover_rate)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">总资产(亿元)</div>
                    <div class="info-value">${formatNumber(stock.total_assets)}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">净资产(亿元)</div>
                    <div class="info-value">${formatNumber(stock.net_assets)}</div>
                </div>
            </div>

            <div class="chart-container">
                <h3 style="margin-bottom: 15px;">K线图 (最近90天)</h3>
                <div id="klineChart" class="chart"></div>
            </div>

            <div class="chart-container">
                <h3 style="margin-bottom: 15px;">成交量</h3>
                <div id="volumeChart" class="chart" style="height: 250px;"></div>
            </div>
        `;

        // 绘制K线图
        if (klineData.success) {
            renderKlineChart(klineData.data);
        }

    } catch (error) {
        console.error('加载股票详情失败:', error);
        content.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    }
}

// 渲染K线图
function renderKlineChart(data) {
    const klineChart = echarts.init(document.getElementById('klineChart'));
    const volumeChart = echarts.init(document.getElementById('volumeChart'));

    // K线图配置
    const klineOption = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function (params) {
                const param = params[0];
                const value = param.data;
                return `
                    日期: ${param.name}<br/>
                    开盘: ${value[1]}<br/>
                    收盘: ${value[2]}<br/>
                    最低: ${value[3]}<br/>
                    最高: ${value[4]}
                `;
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            bottom: '15%'
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
        },
        yAxis: {
            scale: true,
            splitArea: {
                show: true
            }
        },
        dataZoom: [
            {
                type: 'inside',
                start: 50,
                end: 100
            },
            {
                show: true,
                type: 'slider',
                top: '90%',
                start: 50,
                end: 100
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: data.kline,
                itemStyle: {
                    color: '#ef5350',
                    color0: '#26a69a',
                    borderColor: '#ef5350',
                    borderColor0: '#26a69a'
                }
            }
        ]
    };

    // 成交量图配置
    const volumeOption = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            bottom: '15%'
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                show: false
            }
        },
        yAxis: {
            type: 'value',
            splitLine: {
                show: false
            }
        },
        dataZoom: [
            {
                type: 'inside',
                start: 50,
                end: 100
            },
            {
                show: true,
                type: 'slider',
                top: '90%',
                start: 50,
                end: 100
            }
        ],
        series: [
            {
                name: '成交量',
                type: 'bar',
                data: data.volume,
                itemStyle: {
                    color: '#667eea'
                }
            }
        ]
    };

    klineChart.setOption(klineOption);
    volumeChart.setOption(volumeOption);

    // 响应式
    window.addEventListener('resize', () => {
        klineChart.resize();
        volumeChart.resize();
    });
}

// =============== 初始化 ===============

window.onload = function() {
    loadStats();
    document.getElementById('messageInput').focus();

    // 每30秒刷新一次统计信息
    setInterval(loadStats, 30000);

    // 监听Enter键在详情页面搜索
    document.getElementById('detailStockCode').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            loadStockDetail();
        }
    });
};
