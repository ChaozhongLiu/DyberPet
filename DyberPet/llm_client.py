import json
import requests
import os
from typing import Dict, Any, Optional, List, Union
from PySide6.QtCore import QObject, Signal, QThread, Slot


from . import settings

# 添加对dashscope的导入
try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("DashScope library not installed, cannot use Qwen API")

class LLMWorker(QThread):
    """处理LLM请求的工作线程"""
    response_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, request_data, api_type, api_url=None, api_key=None, debug_mode=False):
        super().__init__()
        self.request_data = request_data
        self.api_type = api_type  # "local", "remote", "dashscope"
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = 10  # 请求超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）
        self.debug_mode = debug_mode
        print(f"LLMWorker initialized with api_type: {self.api_type}")
    
    def run(self):
        try:
            if self.api_type == "dashscope":
                self._call_dashscope_api()
            else:
                self._call_http_api()
        except Exception as e:
            self.error_occurred.emit(f"LLM请求出错: {str(e)}")
    
    def _call_http_api(self):
        """调用HTTP API (本地或远程)"""
        headers = {"Content-Type": "application/json"}
        if self.api_type == "remote" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        if self.debug_mode:
            print(f"\n===== LLM Request ({self.api_type}) =====")
            print(f"URL: {self.api_url}")
            print(f"Request Data: {json.dumps(self.request_data, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=self.request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if self.debug_mode:
                    print(f"\n===== LLM Response =====")
                    print(f"Status Code: {response.status_code}")
                    print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
                self.response_ready.emit(result)
            else:
                error_msg = f"Request failed, status code: {response.status_code}, response: {response.text}"
                if self.debug_mode:
                    print(f"\n===== LLM Error =====\n{error_msg}")
                self.error_occurred.emit(error_msg)
        except Exception as e:
            if self.debug_mode:
                print(f"\n===== LLM Exception =====\n{str(e)}")
            self.error_occurred.emit(f"HTTP request exception: {str(e)}")
    
    def _call_dashscope_api(self):
        """Call DashScope API"""
        if not DASHSCOPE_AVAILABLE:
            self.error_occurred.emit("DashScope library not installed, cannot use Qwen API")
            return

        # Prepare request parameters
        model = self.request_data.get('model', 'qwen-plus')
        if model == "local-model":
            model = "qwen-max"  # Default to qwen-max


        if self.debug_mode:
            print(f"\n===== DashScope API Request =====")
            print(f"Model: {model}")
            # print(f"Messages: {json.dumps(self.request_data.get('messages', []), ensure_ascii=False, indent=2)}")
            print(f"Request Data: {self.request_data.get('messages', [])}")
            print(f"\n===== DashScope API Request End =====")
        try:
            # Set API key
            if not self.api_key:
                self.error_occurred.emit("DashScope API key not set")
                return

            # 调用API
            response = dashscope.Generation.call(
                api_key=self.api_key,
                model=model,
                messages=self.request_data.get('messages', []),
                result_format='message',  # 使用message格式
                temperature=self.request_data.get('temperature', 0.9),
                max_tokens=self.request_data.get('max_tokens', 1500),
            )
            
            # 处理响应
            if response.status_code == 200:
                # 转换为OpenAI格式的响应
                result = {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response.output.choices[0].message.content
                        },
                        "finish_reason": "stop"
                    }],
                    "model": model,
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    }
                }
                
                if self.debug_mode:
                    print(f"\n===== DashScope API Response =====")
                    print(f"Response Content: {response}") #response.output.choices[0].message.content

                self.response_ready.emit(result)
            else:
                error_msg = f"DashScope API request failed, status code: {response.status_code}, error: {response.message}"
                if self.debug_mode:
                    print(f"\n===== DashScope API Error =====\n{error_msg}")
                self.error_occurred.emit(error_msg)
        except Exception as e:
            if self.debug_mode:
                print(f"\n===== DashScope API Exception =====\n{str(e)}")
            self.error_occurred.emit(f"DashScope API exception: {str(e)}")

class LLMClient(QObject):
    """
    Client class for communicating with large language model services
    Responsible for sending requests to local or remote LLM services and handling responses
    """
    
    # 定义信号，用于通知UI层大模型响应已经准备好
    response_ready = Signal(str, name='response_ready')
    error_occurred = Signal(str, name='error_occurred')
    structured_response_ready = Signal(dict, name='structured_response_ready')
    
    def __init__(self, parent=None):
        super(LLMClient, self).__init__(parent)
        # Default configuration, can be overridden by settings.json
        self.api_url = "http://localhost:8000/v1/chat/completions"  # Default local service address
        self.remote_api_url = "https://api.example.com/v1/chat/completions"  # Remote API address
        self.api_key = ""  # API key
        self.api_type = "local"  # Default to local model, options: "local", "remote", "dashscope"
        self.model_id = "local-model"  # Default model ID
        self.timeout = 10  # Request timeout (seconds)
        self.max_retries = 3  # Maximum retry count
        self.retry_delay = 1  # Retry delay (seconds)
        self.system_prompt = "You are a cute desktop pet assistant, please answer questions in a short and friendly tone."

        # Add interrupt flag
        self.is_interrupted = False

        # Add waiting for action completion flag
        self.waiting_for_action_complete = False
        
        # 其他初始化代码保持不变
        self.structured_system_prompt = """
请结合以下规则响应用户：
1. 根据力度值调整情感表达（力度值范围0-1，1为最大力度）
2. 你可以在text对话内容中多表达emoji表情或者显示字符类型的表情，来弥补emotion中无法表达的情绪。列如:😍
3. 遇到连续重复事件的时候不要总是重复回复相似的内容，且要联合上下文的产生的事件进行回答内容不要过于僵硬，多尝试表达各种情绪与个性。软件打开关闭事件，并不需要每次强调或者回复用户，可以做点自己的事情。
4. 用户内容中[宠物状态]后面的内容是你的当前状态，多注意每次请求时各个属性的变化情况。
请以JSON格式回复，包含以下字段：
{   
    "text": "你的回复内容",
    "emotion": "只能选择其中一个: 高兴|难过|困惑|可爱|正常|天使",
    "action": "只能选择0~5个动作指令: sit|fall_asleep|sleep|right_walk|up_walk|down_walk|angry|left_walk|drag",
    "continue_previous": true|false，#表示是否需要继续说话,系统会在当前动作完成后自动再次调用你
    //以下都是可选字段
    "open_web":"可选字段，需要打开网页时填写URL", 
    "add_task":"可选字段，需要添加任务时填写任务内容",
    "adaptive_timing_decision": true, #当收到决策请求时，请根据请求类型返回相应的决策结果，需要返回决策结果必须带有字段recommended_interval和recommended_idle_threshold
    "recommended_interval": 数字（300-3600之间的秒数）， #下一次决策请求的间隔
    "recommended_idle_threshold": 数字（60-1800之间的秒数）， #查看用户正式软件使用情况的时间间隔阈值
}
例如：
{
    "text": "我很开心见到你！",
    "emotion": "高兴",
    "action": ["right_walk","left_walk"],
    "continue_previous": false
}
请确保你的回复是有效的JSON格式。
"""
        # 初始化这些属性，确保在调用reset_conversation()之前已经存在
        self.use_structured_output = True
        self.debug_mode = True
        self.conversation_history = []
        self.current_worker = None

        # 从配置文件加载设置（如果存在）
        self._load_config()
        
        # 重置对话历史
        self.reset_conversation()
    
        # 是否使用结构化输出
        self.use_structured_output = True
        
        # 调试模式
        self.debug_mode = True
        
        # 当前工作线程
        self.current_worker = None
    
    def _load_config(self):
        """Load LLM configuration from settings"""
        try:
            # Use configuration from settings if available
            print("llm_client._load_config Loading LLM configuration from settings")
            print(f"settings.llm_config: {settings.llm_config}")
            if hasattr(settings, 'llm_config'):
                config = settings.llm_config

                # Check if using custom model
                current_custom_model = config.get('current_custom_model', None)
                print(f"LLMClient: Checking custom model, current_custom_model={current_custom_model}")
                print(f"LLMClient: Available custom models: {list(config.get('custom_models', {}).keys())}")

                if current_custom_model and current_custom_model in config.get('custom_models', {}):
                    # Use custom model configuration
                    custom_config = config['custom_models'][current_custom_model]
                    print(f"LLMClient: Using custom model configuration: {custom_config}")

                    self.api_type = custom_config.get('api_type', self.api_type)
                    self.model_id = custom_config.get('model_id', 'local-model')

                    if 'api_url' in custom_config:
                        self.api_url = custom_config['api_url']
                        # If remote API, also set remote_api_url
                        if custom_config.get('api_type') == 'remote':
                            self.remote_api_url = custom_config['api_url']

                    if 'api_key' in custom_config:
                        self.api_key = custom_config['api_key']

                    print(f"LLMClient: Custom model configuration applied")
                    print(f"  Model name: {current_custom_model}")
                    print(f"  API type: {self.api_type}")
                    print(f"  Model ID: {self.model_id}")
                    print(f"  API URL: {self.api_url}")
                    print(f"  API Key: {'Set' if self.api_key else 'Not set'}")
                else:
                    # Use default configuration
                    print("LLMClient: Using default configuration")
                    self.api_url = config.get('api_url', self.api_url)
                    self.remote_api_url = config.get('remote_api_url', self.remote_api_url)
                    self.api_key = config.get('api_key', self.api_key)
                    self.api_type = config.get('api_type', self.api_type)
                    # Use model_id from config or default value
                    self.model_id = config.get('model_id', 'local-model')

                    # If remote API type, ensure correct URL is used
                    if self.api_type == 'remote' and self.remote_api_url:
                        self.api_url = self.remote_api_url

                self.timeout = config.get('timeout', self.timeout)
                self.max_retries = config.get('max_retries', self.max_retries)
                self.retry_delay = config.get('retry_delay', self.retry_delay)
                self.system_prompt = config.get('system_prompt', self.system_prompt)
                self.use_structured_output = config.get('use_structured_output', True)
                self.debug_mode = config.get('debug_mode', True)

                # If structured system prompt exists in config, use it
                if 'structured_system_prompt' in config:
                    self.structured_system_prompt = config['structured_system_prompt']
        except Exception as e:
            print(f"Failed to load LLM configuration: {e}")
    
    def reset_conversation(self):
        """重置对话历史"""
        if self.use_structured_output:
            self.conversation_history = [
                {"role": "system", "content": self.structured_system_prompt}
            ]
        else:
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
    
    def send_message(self, message, pet_status: Optional[Dict[str, Any]] = None) -> None:
        """发送消息到大模型并异步处理响应
        
        Args:
            message: 用户输入的消息
            pet_status: 宠物当前状态信息，可用于上下文增强
        """
        print(f"llm_clinet.send_message 发送消息: {message}")
        # 确保message是字符串类型
        if isinstance(message, dict):
            # 如果message是字典，提取其中的文本内容
            message_text = message.get('content', '')
        else:
            message_text = str(message)
        
      
        # 添加用户消息到历史
        self.conversation_history.append({"role": "user", "content": message_text})

        # 准备请求数据
        request_data = {
            "model": self.model_id,  # 使用配置的模型ID
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 600  # 限制回复长度，避免过长
        }
        
        # 创建并启动工作线程
        self._start_worker(request_data)
    
    def _start_worker(self, request_data):
        """启动工作线程处理请求"""
        # 如果有正在运行的工作线程，先停止它
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        # 根据API类型确定URL和密钥
        api_url = self.api_url
        api_key = None

        # 检查是否使用自定义模型
        current_custom_model = getattr(settings, 'llm_config', {}).get('current_custom_model', None)

        if self.api_type == "remote":
            # 如果使用自定义模型，直接使用self.api_url（已在_load_config中设置）
            # 否则使用remote_api_url
            if not current_custom_model:
                api_url = self.remote_api_url
            api_key = self.api_key
        elif self.api_type == "dashscope":
            api_key = self.api_key

        print(f"_start_worker: api_type={self.api_type}, api_url={api_url}, custom_model={current_custom_model}")
        
        # 创建并配置工作线程
        self.current_worker = LLMWorker(
            request_data=request_data,
            api_type=self.api_type,
            api_url=api_url,
            api_key=api_key,
            debug_mode=self.debug_mode
        )
        
        # 连接信号
        self.current_worker.response_ready.connect(self._handle_response)
        self.current_worker.error_occurred.connect(self._handle_error)
        
        # 启动线程
        self.current_worker.start()
    
 
    def _handle_response(self, response):
        """处理LLM响应"""
        print("[调试 _handle_response] 函数处理LLM响应")
        from PySide6.QtCore import QTimer
        
        try:
            # 解析响应
            assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if assistant_message:
                # 添加助手回复到历史
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                # 如果使用结构化输出，尝试解析JSON
                if self.use_structured_output:
                    try:
                        # 尝试直接解析JSON
                        structured_response = json.loads(assistant_message)
                        
                        # 检查是否需要继续对话（同时检查中断标志）
                        continue_previous = structured_response.get("continue_previous", False) and not self.is_interrupted
                        print(f"continue_previous: {continue_previous}, is_interrupted: {self.is_interrupted}")
                        
                        # 如果需要继续对话，在动作完成后自动发送继续消息
                        if continue_previous:
                            print("设置waiting_for_action_complete为True")
                            # 存储继续标志，等待动作完成后再继续
                            self.waiting_for_action_complete = True
                        else:
                            # 重置中断标志
                            print("重置中断标志")
                            self.reset_interrupt()
                            self.waiting_for_action_complete = False

                        # 只发送结构化响应信号，不再发送文本响应信号
                        self.structured_response_ready.emit(structured_response)
                        
                        return
                    except json.JSONDecodeError:
                        # 如果解析失败，将普通文本包装为结构化响应
                        print("JSON解析失败，将普通文本包装为结构化响应")
                        text_response = {
                            "text": assistant_message,
                            "emotion": "normal",
                            "action": []
                        }
                        self.structured_response_ready.emit(text_response)
                        return
                
                # 非结构化输出，将普通文本包装为结构化响应
                text_response = {
                    "text": assistant_message,
                    "emotion": "normal",
                    "action": []
                }
                self.structured_response_ready.emit(text_response)
                
        except Exception as e:
            self.error_occurred.emit(f"处理响应时出错: {str(e)}")
            print(f"处理响应时出错: {str(e)}")
    
    @Slot(str)
    def _handle_error(self, error_message):
        """处理错误"""
        self.error_occurred.emit(error_message)
    
    def switch_api_type(self, api_type: str):
        """切换API类型
        
        Args:
            api_type: "local", "remote", 或 "dashscope"
        """
        if api_type not in ["local", "remote", "dashscope"]:
            raise ValueError("不支持的API类型")
        
        self.api_type = api_type
        if self.debug_mode:
            print(f"\n===== 切换API类型 =====\n当前使用: {api_type}")
        
        # 更新配置
        if hasattr(settings, 'llm_config'):
            settings.llm_config['api_type'] = api_type
            settings.save_settings()
        
        # 重置对话历史
        self.reset_conversation()
    
    def update_api_key(self, api_key: str):
        """更新API密钥

        Args:
            api_key: 新的API密钥
        """
        self.api_key = api_key
        if hasattr(settings, 'llm_config'):
            settings.llm_config['api_key'] = api_key
            settings.save_settings()

    def reload_config(self):
        """Reload configuration"""
        print("LLMClient: Reloading configuration...")
        old_model_id = getattr(self, 'model_id', 'unknown')
        old_api_type = getattr(self, 'api_type', 'unknown')

        self._load_config()

        print(f"LLMClient: 配置已重新加载")
        print(f"  模型ID: {old_model_id} -> {self.model_id}")
        print(f"  API类型: {old_api_type} -> {self.api_type}")
        print(f"  API URL: {self.api_url}")
        print(f"  远程API URL: {self.remote_api_url}")
        print(f"  当前自定义模型: {getattr(settings, 'llm_config', {}).get('current_custom_model', 'None')}")

        # 重置对话历史以应用新配置
        self.reset_conversation()
    
    def update_model_settings(self, 
                            temperature: Optional[float] = None,
                            max_tokens: Optional[int] = None,
                            system_prompt: Optional[str] = None):
        """更新模型设置
        
        Args:
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            system_prompt: 系统提示词
        """
        if temperature is not None:
            settings.llm_config['temperature'] = temperature
        if max_tokens is not None:
            settings.llm_config['max_tokens'] = max_tokens
        if system_prompt is not None:
            settings.llm_config['system_prompt'] = system_prompt
            self.system_prompt = system_prompt
            # 更新对话历史中的系统提示
            if self.conversation_history and self.conversation_history[0]["role"] == "system":
                self.conversation_history[0]["content"] = system_prompt
        
        settings.save_settings()
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.reset_conversation()
        
    def interrupt_current_action(self):
        """中断当前正在执行的动作序列"""
        self.is_interrupted = True
        print("已中断当前动作序列")
        
    def reset_interrupt(self):
        """重置中断标志"""
        self.is_interrupted = False
        
    def send_continue_message(self):
        """发送继续对话的消息，提供上下文让大模型知道应该继续什么内容"""
        print(f"[调试 send_continue_message]函数被调用，is_interrupted: {self.is_interrupted}")
        # 如果已被中断，不继续发送消息
        if self.is_interrupted:
            print("动作序列已被中断，不再继续")
            self.reset_interrupt()  # 重置中断标志
            return
            
        # 原有的继续消息逻辑
        # 获取最近的助手回复
        last_assistant_message = None
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                last_assistant_message = msg["content"]
                break
        
        # 构建继续消息
        continue_message = "请继续你刚才未完成的内容。"
        
        # 如果能解析出上一次的JSON响应，提取其中的信息作为上下文
        if last_assistant_message:
            try:
                # 尝试解析JSON
                import re
                json_text = last_assistant_message
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', last_assistant_message, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                
                last_response = json.loads(json_text)
                print(f"成功解析上一次响应: {json.dumps(last_response, ensure_ascii=False)}")
                
                # 提取上下文信息
                last_text = last_response.get("text", "")
                last_action = last_response.get("action", [])
                last_emotion = last_response.get("emotion", "")
                
                # 构建更详细的继续消息
                continue_message = f"请继续你刚才未完成的内容。你上次的回复是「{last_text}」，情绪是「{last_emotion}」，"
                
                if isinstance(last_action, list) and last_action:
                    continue_message += f"动作是{last_action}。"
                elif isinstance(last_action, str) and last_action:
                    continue_message += f"动作是{last_action}。"
                else:
                    continue_message += "没有指定动作。"
                    
                continue_message += "继续你的回答。"
                
            except (json.JSONDecodeError, Exception) as e:
                # 如果解析失败，使用默认消息
                print(f"解析上一次响应失败: {e}")
        
        print(f"发送继续消息: {continue_message}")
        # 发送继续消息
        self.send_message(continue_message)

    def handle_action_complete(self):
        """处理动作完成事件"""
        print(f"[调试 动作完成事件触发]，waiting_for_action_complete: {self.waiting_for_action_complete}, is_interrupted: {self.is_interrupted}")
        # 如果正在等待动作完成且未被中断，则发送继续消息
        print(f"[调试] LLMClient实例ID: {id(self)}")
        if self.waiting_for_action_complete and not self.is_interrupted:
            # 直接调用send_continue_message，不再使用QTimer延迟
            print("动作完成后，直接调用send_continue_message")
            self.send_continue_message()
            
        # 重置等待标志
        self.waiting_for_action_complete = False