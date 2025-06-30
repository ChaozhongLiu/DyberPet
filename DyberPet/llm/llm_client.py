import json
import requests
import os
from typing import Dict, Any, Optional, List, Union
from PySide6.QtCore import QObject, Signal, QThread, Slot, QMutex, QWaitCondition
import queue # Added for thread-safe queue

import DyberPet.settings as settings

# 添加对dashscope的导入
try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("未安装dashscope库，无法使用通义千问API")

class LLMWorker(QThread):
    """处理LLM请求的持久工作线程"""
    response_ready = Signal(dict, str)
    error_occurred = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._request_queue = queue.Queue()
        self._should_stop = False
        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()

        # These will be set per request processed by the run loop
        self.current_request_data: Optional[Dict[str, Any]] = None
        self.current_api_type: Optional[str] = None
        self.current_api_url: Optional[str] = None
        self.current_api_key: Optional[str] = None
        self.current_debug_mode: bool = False

    def enqueue_request(self, request_data: Dict[str, Any], api_type: str, api_url: Optional[str], api_key: Optional[str], debug_mode: bool, request_id: Optional[str]):
        """将请求添加到队列中等待处理"""
        self._mutex.lock()
        self._request_queue.put({
            "request_data": request_data,
            "api_type": api_type,
            "api_url": api_url,
            "api_key": api_key,
            "debug_mode": debug_mode,
            "request_id": request_id
        })
        self._wait_condition.wakeOne()  # Wake up the run() method if it's waiting
        self._mutex.unlock()

    def run(self):
        """主工作循环，处理队列中的请求"""
        print("LLMWorker thread started.")
        while True:
            self._mutex.lock()
            if self._should_stop and self._request_queue.empty():
                self._mutex.unlock()
                break  # Exit loop if stop requested and queue is empty

            if self._request_queue.empty():
                self._wait_condition.wait(self._mutex)  # Wait for a new request or stop signal
                self._mutex.unlock()
                continue  # Re-check conditions

            task = self._request_queue.get()
            self._mutex.unlock()  # Unlock mutex before processing task

            try:
                self.current_request_data = task["request_data"]
                self.current_api_type = task["api_type"]
                self.current_api_url = task["api_url"]
                self.current_api_key = task["api_key"]
                self.current_debug_mode = task["debug_mode"]
                self.request_id = task["request_id"]
                
                print(f"LLMWorker processing task with api_type: {self.current_api_type}")

                if self.current_api_type == "dashscope":
                    self._call_dashscope_api()
                else:
                    self._call_http_api()
            except Exception as e:
                # Emit error if task processing itself fails catastrophically
                self.error_occurred.emit(f"LLMWorker task processing error: {str(e)}", self.request_id)
        print("LLMWorker thread finished.")

    def stop(self):
        """停止工作线程"""
        print("LLMWorker.stop() called")
        self._mutex.lock()
        self._should_stop = True
        self._wait_condition.wakeOne()  # Wake run() if it's waiting
        self._mutex.unlock()
        self.wait()  # Wait for QThread.run() to finish
        print("LLMWorker.stop() completed")

    def _call_http_api(self):
        """调用HTTP API (本地或远程)"""
        headers = {"Content-Type": "application/json"}
        if self.current_api_type == "remote" and self.current_api_key:
            headers["Authorization"] = f"Bearer {self.current_api_key}"
        
        if self.current_debug_mode:
            print(f"\n===== LLM请求 ({self.current_api_type}) =====")
            print(f"URL: {self.current_api_url}")
            print(f"请求数据: {json.dumps(self.current_request_data, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                self.current_api_url, # type: ignore
                headers=headers,
                json=self.current_request_data,
                timeout=30 
            )
            
            if response.status_code == 200:
                result = response.json()
                if self.current_debug_mode:
                    print(f"\n===== LLM响应 =====")
                    print(f"状态码: {response.status_code}")
                    print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                self.response_ready.emit(result, self.request_id)
            else:
                error_msg = f"请求失败，状态码: {response.status_code}, 响应: {response.text}"
                if self.current_debug_mode:
                    print(f"\n===== LLM错误 =====\n{error_msg}")
                self.error_occurred.emit(error_msg, self.request_id)
        except Exception as e:
            if self.current_debug_mode:
                print(f"\n===== LLM异常 =====\n{str(e)}")
            self.error_occurred.emit(f"HTTP请求异常: {str(e)}", self.request_id)
    
    def _call_dashscope_api(self):
        """调用通义千问API"""
        if not DASHSCOPE_AVAILABLE:
            self.error_occurred.emit("未安装dashscope库，无法使用通义千问API", self.request_id)
            return

        model = self.current_request_data.get('model', 'qwen-plus') # type: ignore
        if model == "local-model":
            model = "qwen-max"
        
        if self.current_debug_mode:
            print(f"\n===== 通义千问API请求 =====")
            print(f"模型: {model}")
            print(f"请求数据: {self.current_request_data.get('messages', [])}") # type: ignore
            print(f"\n===== 通义千问API请求 结束 =====")
        try:
            if not self.current_api_key:
                self.error_occurred.emit("未设置通义千问API密钥", self.request_id)
                return

            response = dashscope.Generation.call(
                api_key=self.current_api_key,
                model=model,
                messages=self.current_request_data.get('messages', []), # type: ignore
                result_format='message',
                temperature=self.current_request_data.get('temperature', 0.9), # type: ignore
                max_tokens=self.current_request_data.get('max_tokens', 1500), # type: ignore
            )
            
            if response.status_code == 200:
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
                if self.current_debug_mode:
                    print(f"\n===== 通义千问API响应 =====")
                    print(f"响应内容: {response}")
                self.response_ready.emit(result, self.request_id)
            else:
                error_msg = f"通义千问API请求失败，状态码: {response.status_code}, 错误: {response.message}"
                if self.current_debug_mode:
                    print(f"\n===== 通义千问API错误 =====\n{error_msg}")
                self.error_occurred.emit(error_msg, self.request_id)
        except Exception as e:
            if self.current_debug_mode:
                print(f"\n===== 通义千问API异常 =====\n{str(e)}")
            self.error_occurred.emit(f"通义千问API异常: {str(e)}", self.request_id)

class LLMClient(QObject):
    """
    与大模型服务通信的客户端类
    负责发送请求到本地或远程大模型服务并处理响应
    """
    error_occurred = Signal(str, str, name='error_occurred')
    structured_response_ready = Signal(dict, str, name='structured_response_ready')
    
    def __init__(self, parent=None):
        super(LLMClient, self).__init__(parent)

        self.api_url = "http://localhost:8000/v1/chat/completions"
        self.remote_api_url = "https://api.example.com/v1/chat/completions"
        self.api_key = ""
        self.api_type = "Qwen"
        self.timeout = 10 
        self.max_retries = 3
        self.retry_delay = 1
        self.is_interrupted = False
        self.waiting_for_action_complete = False
        
        self.schema_prompt = """
请结合以下规则响应用户：
1. 根据力度值调整情感表达（力度值范围0-1，1为最大力度）
2. 你可以在text对话内容中多表达emoji表情或者显示字符类型的表情，来弥补emotion中无法表达的情绪。列如:😍
3. 遇到连续重复事件的时候不要总是重复回复相似的内容，且要联合上下文的产生的事件进行回答内容不要过于僵硬，多尝试表达各种情绪与个性。软件打开关闭事件，并不需要每次强调或者回复用户，可以做点自己的事情。
4. 用户内容中[宠物状态]后面的内容是你的当前状态，多注意每次请求时各个属性的变化情况。
5. 根据用户说的语言，使用相同语言在text字段回复（中文→中文，英文→英文，日文→日文）
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
        self.structured_system_prompt = self.schema_prompt
        self.use_structured_output = True
        self.debug_mode = True 
        self.conversation_history: List[Dict[str,str]] = []

        self._load_config()
        self.reset_conversation()
        
        self._worker = LLMWorker()
        self._worker.response_ready.connect(self._handle_response)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()
            
    def _load_config(self):
        """从settings加载LLM配置"""
        try:
            print("llm_client._load_config 从settings加载LLM配置", settings.llm_config)
            if hasattr(settings, 'llm_config'):
                config = settings.llm_config
                self.api_type = config.get('api_type', self.api_type)
                self.model_type = config.get('model_type', None)
                self.timeout = config.get('timeout', self.timeout)
                self.max_retries = config.get('max_retries', self.max_retries)
                self.retry_delay = config.get('retry_delay', self.retry_delay)
                self.debug_mode = config.get('debug_mode', self.debug_mode)
                self.structured_system_prompt = settings.pet_conf.prompt +"当前用户语言环境是"+settings.language_code+ self.schema_prompt
                self.api_key = config.get('api_key', self.api_key)

                self.api_url = config.get('api_url', self.api_url)
                self.remote_api_url = config.get('remote_api_url', self.remote_api_url)
                
            if self.model_type == 'Qwen':
                self.api_type = 'dashscope'
            else:
                self.api_type = 'local' if self.api_type == 'local' else 'remote'
        except Exception as e:
            print(f"加载LLM配置失败: {e}")
    
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
    
    def send_message(self, message: Union[str, Dict[str, Any]], request_id: str) -> None:
        """发送消息到大模型并异步处理响应"""
        print(f"llm_client.send_message 发送消息: {message}")
        message_text: str
        if isinstance(message, dict):
            message_text = message.get('content', '')
        else:
            message_text = str(message)
        
        self.conversation_history.append({"role": "user", "content": message_text})

        request_data = {
            "model": "local-model", 
            "messages": self.conversation_history,
            "temperature": settings.llm_config.get('temperature', 0.7) if hasattr(settings, 'llm_config') else 0.7,
            "max_tokens": settings.llm_config.get('max_tokens', 600) if hasattr(settings, 'llm_config') else 600
        }
        
        self._submit_request_to_worker(request_data, request_id)
    
    def _submit_request_to_worker(self, request_data: Dict[str, Any], request_id: str):
        """将请求数据提交给持久工作线程"""
        api_url_to_use: Optional[str] = self.api_url
        api_key_to_use: Optional[str] = None
        
        if self.api_type == "remote":
            api_url_to_use = self.remote_api_url
            api_key_to_use = self.api_key
        elif self.api_type == "dashscope":
            api_url_to_use = None # Dashscope API client handles URL internally
            api_key_to_use = self.api_key
        
        self._worker.enqueue_request(
            request_data=request_data,
            api_type=self.api_type,
            api_url=api_url_to_use,
            api_key=api_key_to_use,
            debug_mode=self.debug_mode,
            request_id=request_id
        )
 
    def _handle_response(self, response: Dict[str, Any], request_id: str):
        """处理LLM响应"""
        print("[调试 _handle_response] 函数处理LLM响应")
        try:
            assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if assistant_message:
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                if self.use_structured_output:
                    try:
                        structured_response = json.loads(assistant_message)
                        continue_previous = structured_response.get("continue_previous", False) and not self.is_interrupted
                        print(f"continue_previous: {continue_previous}, is_interrupted: {self.is_interrupted}")
                        
                        if continue_previous:
                            print("设置waiting_for_action_complete为True")
                            self.waiting_for_action_complete = True
                        else:
                            print("重置中断标志")
                            self.reset_interrupt()
                            self.waiting_for_action_complete = False
                        self.structured_response_ready.emit(structured_response, request_id)
                        return
                    except json.JSONDecodeError:
                        print("JSON解析失败，将普通文本包装为结构化响应")
                        text_response = {
                            "text": assistant_message, "emotion": "normal", "action": []
                        }
                        self.structured_response_ready.emit(text_response, request_id)
                        return
                
                text_response = {
                    "text": assistant_message, "emotion": "normal", "action": []
                }
                self.structured_response_ready.emit(text_response, request_id)
        except Exception as e:
            error_msg = f"处理响应时出错: {str(e)}"
            self.error_occurred.emit(error_msg, request_id)
            print(error_msg)
    
    @Slot(str)
    def _handle_error(self, error_message: str, request_id: str):
        """处理错误"""
        self.error_occurred.emit(error_message, request_id)
    
        
    def interrupt_current_action(self):
        """中断当前正在执行的动作序列 (client-side logic)"""
        self.is_interrupted = True
        print("已中断当前动作序列")
        # Note: This does not interrupt a network request already in progress in the worker.
        
    def reset_interrupt(self):
        """重置中断标志"""
        self.is_interrupted = False
        
    def send_continue_message(self):
        """发送继续对话的消息"""
        print(f"[调试 send_continue_message]函数被调用，is_interrupted: {self.is_interrupted}")
        if self.is_interrupted:
            print("动作序列已被中断，不再继续")
            self.reset_interrupt()
            return
            
        last_assistant_message_content: Optional[str] = None
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                last_assistant_message_content = msg["content"]
                break
        
        continue_message = "请继续你刚才未完成的内容。"
        if last_assistant_message_content:
            try:
                import re
                json_text = last_assistant_message_content
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', last_assistant_message_content, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                
                last_response = json.loads(json_text)
                last_text = last_response.get("text", "")
                last_action = last_response.get("action", [])
                last_emotion = last_response.get("emotion", "")
                
                continue_message = f"请继续你刚才未完成的内容。你上次的回复是「{last_text}」，情绪是「{last_emotion}」，"
                action_str = ""
                if isinstance(last_action, list) and last_action:
                    action_str = f"动作是{last_action}。"
                elif isinstance(last_action, str) and last_action:
                    action_str = f"动作是{last_action}。"
                else:
                    action_str = "没有指定动作。"
                continue_message += action_str + "继续你的回答。"
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析上一次响应失败: {e}")
        
        print(f"发送继续消息: {continue_message}")
        self.send_message(continue_message)

    def handle_action_complete(self):
        return
        """处理动作完成事件"""
        print(f"[调试 动作完成事件触发]，waiting_for_action_complete: {self.waiting_for_action_complete}, is_interrupted: {self.is_interrupted}")
        print(f"[调试] LLMClient实例ID: {id(self)}")
        if self.waiting_for_action_complete and not self.is_interrupted:
            print("动作完成后，直接调用send_continue_message")
            self.send_continue_message()
        self.waiting_for_action_complete = False

    def close(self):
        """停止LLM工作线程并进行清理"""
        if hasattr(self, '_worker') and self._worker is not None:
            print("Closing LLMClient, stopping worker...")
            self._worker.stop()
            print("LLMWorker stopped by LLMClient.close()")

    def change_model(self):
        self.model_type = settings.llm_config.get('model_type', None)
        if self.model_type == 'Qwen':
            self.api_type = 'dashscope'
        else:
            self.api_type = 'remote'
        print(f"切换模型为{self.model_type}")
        self.reset_conversation()

    def change_debug_mode(self):
        self.debug_mode = settings.llm_config.get('debug_mode', False)
        print(f"切换调试模式为{self.debug_mode}")
    
    def switch_api_type(self, api_type: str):
        """切换API类型"""
        if api_type not in ["local", "remote", "dashscope"]:
            raise ValueError("不支持的API类型")
        
        self.api_type = api_type
        if self.debug_mode:
            print(f"\n===== 切换API类型 =====\n当前使用: {api_type}")
        
        if hasattr(settings, 'llm_config'):
            settings.llm_config['api_type'] = api_type
            settings.save_settings()
        self.reset_conversation()

    
    def update_api_key(self):
        self.api_key = settings.llm_config.get('api_key', '')
        print(f"更新API密钥为{self.api_key}")
    
    """
    def update_model_settings(self, 
                            temperature: Optional[float] = None,
                            max_tokens: Optional[int] = None,
                            system_prompt: Optional[str] = None):
        '''更新模型设置'''
        if hasattr(settings, 'llm_config'):
            if temperature is not None:
                settings.llm_config['temperature'] = temperature
            if max_tokens is not None:
                settings.llm_config['max_tokens'] = max_tokens
            if system_prompt is not None:
                settings.llm_config['system_prompt'] = system_prompt
                self.system_prompt = system_prompt
                if self.conversation_history and self.conversation_history[0]["role"] == "system" and not self.use_structured_output:
                    self.conversation_history[0]["content"] = system_prompt
                # If using structured output, structured_system_prompt might also need update or re-evaluation
            settings.save_settings()
            self.reset_conversation() # Reset to apply new system prompt if changed
    """
