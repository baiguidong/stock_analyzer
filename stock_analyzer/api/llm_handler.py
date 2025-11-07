"""
LLM 处理器 - 支持多种大模型
"""
from typing import List, Dict, Any, Optional
import json
import logging

from ..config import config
from ..tools import StockTools, get_stock_tools_definitions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMHandler:
    """LLM 处理器，支持 OpenAI、Anthropic、Ollama"""

    def __init__(self, stock_tools: StockTools):
        self.stock_tools = stock_tools
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.tools_definitions = get_stock_tools_definitions()

        # 初始化客户端
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"不支持的 LLM provider: {self.provider}")

    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
            logger.info(f"已初始化 OpenAI 客户端，模型: {self.model}")
        except ImportError:
            logger.error("请安装 openai: pip install openai")
            raise

    def _init_anthropic(self):
        """初始化 Anthropic 客户端"""
        try:
            from anthropic import Anthropic

            self.client = Anthropic(api_key=config.llm.api_key)
            logger.info(f"已初始化 Anthropic 客户端，模型: {self.model}")
        except ImportError:
            logger.error("请安装 anthropic: pip install anthropic")
            raise

    def _init_ollama(self):
        """初始化 Ollama 客户端"""
        try:
            import ollama

            self.client = ollama
            logger.info(f"已初始化 Ollama 客户端，模型: {self.model}")
        except ImportError:
            logger.error("请安装 ollama: pip install ollama")
            raise

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用工具函数"""
        try:
            if tool_name == "search_stock":
                return self.stock_tools.search_stock(**arguments)
            elif tool_name == "get_stock_detail":
                return self.stock_tools.get_stock_detail(**arguments)
            elif tool_name == "get_stock_history":
                return self.stock_tools.get_stock_history(**arguments)
            elif tool_name == "filter_stocks":
                return self.stock_tools.filter_stocks(**arguments)
            elif tool_name == "execute_sql_query":
                return self.stock_tools.execute_sql_query(**arguments)
            elif tool_name == "get_database_stats":
                return self.stock_tools.get_database_stats(**arguments)
            else:
                return json.dumps({"error": f"未知的工具: {tool_name}"}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def chat(self, messages: List[Dict[str, str]], max_iterations: int = 5) -> Dict[str, Any]:
        """
        与 LLM 对话，支持 Function Calling

        Args:
            messages: 对话消息列表
            max_iterations: 最大迭代次数（防止无限循环）

        Returns:
            LLM 响应
        """
        if self.provider == "openai":
            return self._chat_openai(messages, max_iterations)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, max_iterations)
        elif self.provider == "ollama":
            return self._chat_ollama(messages, max_iterations)

    def _chat_openai(self, messages: List[Dict[str, str]], max_iterations: int) -> Dict[str, Any]:
        """OpenAI 对话"""
        conversation = messages.copy()

        for iteration in range(max_iterations):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=conversation,
                    tools=self.tools_definitions,
                    tool_choice="auto"
                )

                message = response.choices[0].message

                # 如果没有工具调用，直接返回
                if not message.tool_calls:
                    return {
                        "content": message.content,
                        "tool_calls": None
                    }

                # 处理工具调用
                conversation.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })

                # 执行工具调用
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    logger.info(f"调用工具: {function_name}({arguments})")

                    # 调用工具
                    result = self._call_tool(function_name, arguments)

                    # 添加工具响应
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                # 继续对话，让 LLM 处理工具结果

            except Exception as e:
                logger.error(f"OpenAI 对话失败: {e}")
                return {
                    "content": f"对话失败: {str(e)}",
                    "tool_calls": None
                }

        # 达到最大迭代次数
        return {
            "content": "对话超过最大迭代次数",
            "tool_calls": None
        }

    def _chat_anthropic(self, messages: List[Dict[str, str]], max_iterations: int) -> Dict[str, Any]:
        """Anthropic Claude 对话"""
        # Anthropic 的工具格式不同
        tools = [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            }
            for tool in self.tools_definitions
        ]

        conversation = messages.copy()

        for iteration in range(max_iterations):
            try:
                # 分离系统消息
                system_message = ""
                user_messages = []
                for msg in conversation:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_message if system_message else None,
                    messages=user_messages,
                    tools=tools
                )

                # 处理响应
                if response.stop_reason == "end_turn":
                    # 正常结束
                    content = ""
                    for block in response.content:
                        if block.type == "text":
                            content += block.text
                    return {"content": content, "tool_calls": None}

                elif response.stop_reason == "tool_use":
                    # 需要调用工具
                    conversation.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._call_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                    conversation.append({
                        "role": "user",
                        "content": tool_results
                    })

            except Exception as e:
                logger.error(f"Anthropic 对话失败: {e}")
                return {"content": f"对话失败: {str(e)}", "tool_calls": None}

        return {"content": "对话超过最大迭代次数", "tool_calls": None}

    def _chat_ollama(self, messages: List[Dict[str, str]], max_iterations: int) -> Dict[str, Any]:
        """Ollama 对话（简化版，可能不支持工具调用）"""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages
            )

            return {
                "content": response['message']['content'],
                "tool_calls": None
            }

        except Exception as e:
            logger.error(f"Ollama 对话失败: {e}")
            return {
                "content": f"对话失败: {str(e)}",
                "tool_calls": None
            }
