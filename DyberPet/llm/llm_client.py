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
    error_occurred = Signal(dict, str)

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
                if self.current_debug_mode:
                    print(f"\n===== LLMWorker task processing error =====\n{str(e)}")
                self.error_occurred.emit({"code": "E001", "details": str(e)}, self.request_id)
        print("LLMWorker thread finished.")

    def stop(self):
        """停止工作线程"""
        print("LLMWorker.stop() called")
        self._mutex.lock()
        self._should_stop = True
        self._wait_condition.wakeOne()  # Wake run() if it's waiting
        self._mutex.unlock()
        
        # Wait for the thread to finish, but with a timeout
        if not self.wait(1000):  # Wait up to 5 seconds
            print("LLMWorker thread did not stop gracefully, terminating...")
            self.terminate()
            self.wait(1000)  # Wait another second for termination
        
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
                if self.current_debug_mode:
                    print(f"\n===== LLM错误 =====\n请求失败，状态码: {response.status_code}, 响应: {response.text}")
                self.error_occurred.emit({"code": "E002", "details": f"状态码: {response.status_code}, 响应: {response.text}"}, self.request_id)
        except Exception as e:
            if self.current_debug_mode:
                print(f"\n===== LLM异常 =====\n{str(e)}")
            self.error_occurred.emit({"code": "E003", "details": str(e)}, self.request_id)
    
    def _call_dashscope_api(self):
        """调用通义千问API"""
        if not DASHSCOPE_AVAILABLE:
            if self.current_debug_mode:
                print(f"\n===== Dashscope未安装 =====")
            self.error_occurred.emit({"code": "E004", "details": None}, self.request_id)
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
                if self.current_debug_mode:
                    print(f"\n===== Dashscope未设置API密钥 =====")
                self.error_occurred.emit({"code": "E005", "details": None}, self.request_id)
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
                if self.current_debug_mode:
                    print(f"\n===== 通义千问API错误 =====\n状态码: {response.status_code}, 错误: {response.message}")
                self.error_occurred.emit({"code": "E006", "details": f"状态码: {response.status_code}, 错误: {response.message}"}, self.request_id)
        except Exception as e:
            if self.current_debug_mode:
                print(f"\n===== 通义千问API异常 =====\n{str(e)}")
            self.error_occurred.emit({"code": "E007", "details": str(e)}, self.request_id)

class LLMClient(QObject):
    """
    与大模型服务通信的客户端类
    负责发送请求到本地或远程大模型服务并处理响应
    """
    error_occurred = Signal(dict, str, name='error_occurred')
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
        # self.is_interrupted = False
        # self.waiting_for_action_complete = False
        
        # Track active request IDs to handle responses from previous pets
        self._active_requests = {}

        self.schema_prompt = """
请遵循以下指导原则：
## 请求上下文信息

### 事件类型
你将会收到包含以下一种或多种事件类型的请求：
- [用户交互事件]：用户对话、点击、拖拽等
- [状态变化事件]：饱食度、好感度等属性变化
- [时间触发事件]：定时触发的事件
- [环境感知事件]：系统环境变化
- [随机触发事件]：随机触发的特殊事件

### 宠物状态
每次请求都会包含：宠物名称、饱食度(hp:0-100)、好感度(fv:0-120)、好感度等级(fv_lvl)、时间、位置坐标等状态信息

## 响应格式要求
请严格按照以下JSON格式回复，确保所有字段类型正确：

```json
{
    "text": "你的回复内容（可使用'<sep>'分隔多条消息）", // 回复文字内容，支持使用'<sep>'标记分隔多条消息
    "emotion": "高兴|难过|困惑|可爱|正常|天使", // 必须从上述指定的6种情绪中选择一种
    "action": ["动作3","动作1"], // 动作指令数组，最多3个，从可用动作中选择，如果不需要动作，请使用空数组[]
    //以下都是可选字段
    "open_web": "可选：需要打开网页时填写完整URL", // 可选字段，需要打开网页时填写完整URL
    "add_task": "可选：需要添加任务时填写任务内容", // 可选字段，需要添加任务时填写具体任务内容
    "adaptive_timing_decision": true, // 布尔值，用于调整软件监控相关的参数，决策请求时设为true
    "recommended_interval": 300-3600, // 软件监控参数，下次决策间隔（300-3600秒）
    "recommended_idle_threshold": 60-1800 // 软件监控参数，空闲检测阈值（60-1800秒）
}
```

## 可用动作列表
当前可用的动作包括：ACTION_LIST

## 示例回复
{
    "text": "你回来啦！😊 <sep>今天想和我聊什么呢？",
    "emotion": "高兴",
    "action": []
}
注意：请不要带上```json```标签，直接返回JSON格式

## 行为指导
1. **动作使用策略**：只在真正需要时才使用动作，保持低频率（约20%的回复中使用动作），避免过度使用
2. **点击交互**：用户点击行为会提供给你交互强度（0-1范围），如果有交互强度，可以根据此调整情感表达
3. **表情丰富**：在text对话中多使用emoji表情，弥补emotion字段的局限性
4. **避免重复**：遇到连续重复事件时，不要总是回复相似内容，要结合上下文和个性特点
5. **状态感知**：注意用户内容中[宠物状态]后的属性变化，据此调整回应
6. **格式要求**：确保回复是有效的JSON格式，软件监控参数调整时 (adaptive_timing_decision: true)，请保持 text 和 action 字段为空
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
                self.api_key = config.get('api_key', self.api_key)
                self.api_url = config.get('api_url', self.api_url)
                self.remote_api_url = config.get('remote_api_url', self.remote_api_url)
                
            if self.model_type == 'Qwen':
                self.api_type = 'dashscope'
            else:
                self.api_type = 'local' if self.api_type == 'local' else 'remote'
                
            # 更新系统提示词
            self._update_system_prompt()
        except Exception as e:
            print(f"加载LLM配置失败: {e}")
    
    def _get_available_actions(self) -> List[str]:
        """获取当前宠物可用的动作列表"""
        try:
            if not hasattr(settings, 'act_data') or not hasattr(settings, 'petname'):
                return []
            
            act_configs = settings.act_data.allAct_params.get(settings.petname, {})
            available_actions = []
            
            for act_name, act_conf in act_configs.items():
                # 只包含已解锁的动作，且避免系统动作
                if (act_conf.get('unlocked', False) and 
                    -1 not in act_conf.get('status_type', [0, 0])):
                    available_actions.append(act_name)
            
            return available_actions
        except Exception as e:
            print(f"获取可用动作失败: {e}")
            return []
    
    def _update_system_prompt(self):
        """更新提示词中的动作列表"""
        try:
            available_actions = self._get_available_actions()
            action_list_str = ', '.join(f'"{action}"' for action in available_actions)
            
            # 更新schema_prompt中的动作列表
            updated_schema = self.schema_prompt.replace('ACTION_LIST', f'{action_list_str}')
            
            # 更新系统提示词
            if hasattr(settings, 'pet_conf') and settings.pet_conf.prompt:
                role_prompt = settings.pet_conf.prompt
            else:
                role_prompt = "你是一个智能的桌面宠物，需要根据用户交互和系统事件做出简短友好的回应。\n"
                        
            # 用户昵称
            usertag = settings.usertag_dict.get(settings.petname, "")
            if usertag:
                nickname_prompt = f"\n8.**用户昵称**：用户希望你称呼TA为{usertag}。"
            else:
                nickname_prompt = ""
            
            self.structured_system_prompt = role_prompt + updated_schema + \
                f"7. **语言匹配**：与用户语言设置保持一致，除非用户明确要求使用其他语言，当前用户语言设置是{settings.language_code}" + \
                nickname_prompt
            
            if self.debug_mode:
                print(f"[LLM Client] 更新角色提示词: {role_prompt}")
                print(f"[LLM Client] 更新动作列表: {action_list_str}")
                print(f"[LLM Client] 用户昵称: {usertag}")
                
        except Exception as e:
            print(f"更新系统提示词失败: {e}")
    
    def reset_conversation(self):
        """重置对话历史"""
        # 清理所有活跃请求
        self._cleanup_all_requests()
        # 重置对话历史
        self.conversation_history = [
            {"role": "system", "content": self.structured_system_prompt}
        ]
    
    def send_message(self, message: Union[str, Dict[str, Any]], request_id: str) -> None:
        """发送消息到大模型并异步处理响应"""
        print(f"llm_client.send_message 发送消息: {message}")
        message_text: str
        if isinstance(message, dict):
            message_text = message.get('content', '')
        else:
            message_text = str(message)
        
        # Store the user message and track the request
        self._active_requests[request_id] = {
            "message": {"role": "user", "content": message_text}
        }

        request_data = {
            "model": "local-model", 
            "messages": self.conversation_history + [self._active_requests[request_id]["message"]],
            "temperature": settings.llm_config.get('temperature', 0.8) if hasattr(settings, 'llm_config') else 0.8,
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
        
        # Check if this request is still active (not from a previous pet)
        if not self._is_request_active(request_id):
            return
            
        try:
            assistant_message = self._extract_assistant_message(response)
            if not assistant_message:
                print(f"[LLM Client] 空响应内容，清理请求: {request_id}")
                self._cleanup_request(request_id)
                return
                
            # Process the structured response
            success = self._handle_structured_response(assistant_message, request_id)
            if success:
                self._add_user_message_to_history(request_id)
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
            self._cleanup_request(request_id)
                
        except Exception as e:
            self._handle_error(f"处理响应时出错: {str(e)}", request_id)
    
    def _add_user_message_to_history(self, request_id: str):
        """将指定请求的用户消息添加到对话历史"""
        if request_id in self._active_requests:
            self.conversation_history.append(self._active_requests[request_id]["message"])
            del self._active_requests[request_id]
    
    def _is_request_active(self, request_id: str) -> bool:
        """检查请求是否仍然活跃"""
        if request_id not in self._active_requests:
            print(f"[LLM Client] 忽略未知请求ID的回复: {request_id}")
            return False
        return True
    
    def _extract_assistant_message(self, response: Dict[str, Any]) -> str:
        """从响应中提取助手消息内容"""
        raw_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Strip any ```json and ``` tags only if they appear at start/end
        stripped_content = raw_content.strip().removeprefix("```json").removesuffix("```").strip()
        return stripped_content
    
    def _handle_structured_response(self, assistant_message: str, request_id: str):
        """处理结构化响应"""
        try:
            structured_response = json.loads(assistant_message)
            self.structured_response_ready.emit(structured_response, request_id)
            return True
        except json.JSONDecodeError:
            self._handle_error({"code": "E008", "details": assistant_message[:100] if assistant_message else None}, request_id)
            return False
        except Exception as e:
            self._handle_error({"code": "E009", "details": str(e)}, request_id)
            return False
    
    """
    def _update_continuation_state(self, structured_response: Dict[str, Any]):
        '''更新继续状态'''
        continue_previous = structured_response.get("continue_previous", False) and not self.is_interrupted
        print(f"continue_previous: {continue_previous}, is_interrupted: {self.is_interrupted}")
        
        if continue_previous:
            print("设置waiting_for_action_complete为True")
            self.waiting_for_action_complete = True
        else:
            print("重置中断标志")
            self.reset_interrupt()
            self.waiting_for_action_complete = False
    """
    
    def _handle_error(self, error_message: dict, request_id: str):
        """处理所有错误（包括LLMWorker错误和响应处理错误）"""
        # Check if this request is still active (not from a previous pet)
        if not self._is_request_active(request_id):
            print(f"[LLM Client] 忽略未知请求ID的错误: {request_id}")
            return
            
        print(f"[LLM Client] 处理错误: {error_message}, 请求ID: {request_id}")
        
        self.error_occurred.emit(error_message, request_id)
        # Clean up the request (includes pending message cleanup)
        self._cleanup_request(request_id)
    
    # def interrupt_current_action(self):
    #     """中断当前正在执行的动作序列 (client-side logic)"""
    #     self.is_interrupted = True
    #     print("已中断当前动作序列")
    #     # Note: This does not interrupt a network request already in progress in the worker.
        
    # def reset_interrupt(self):
    #     """重置中断标志"""
    #     self.is_interrupted = False
        
    # def send_continue_message(self):
    #     '''发送继续对话的消息'''
    #     print(f"[调试 send_continue_message]函数被调用，is_interrupted: {self.is_interrupted}")
    #     if self.is_interrupted:
    #         print("动作序列已被中断，不再继续")
    #         self.reset_interrupt()
    #         return
            
    #     last_assistant_message_content: Optional[str] = None
    #     for msg in reversed(self.conversation_history):
    #         if msg["role"] == "assistant":
    #         last_assistant_message_content = msg["content"]
    #         break
        
    #     continue_message = "请继续你刚才未完成的内容。"
    #     if last_assistant_message_content:
    #         try:
    #             import re
    #             json_text = last_assistant_message_content
    #             json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', last_assistant_message_content, re.DOTALL)
    #             if json_match:
    #             json_text = json_match.group(1)
                
    #             last_response = json.loads(json_text)
    #             last_text = last_response.get("text", "")
    #             last_action = last_response.get("action", [])
    #             last_emotion = last_response.get("emotion", "")
                
    #             continue_message = f"请继续你刚才未完成的内容。你上次的回复是「{last_text}」，情绪是「{last_emotion}」，"
    #             action_str = ""
    #             if isinstance(last_action, list) and last_action:
    #                 action_str = f"动作是{last_action}。"
    #             elif isinstance(last_action, str) and last_action:
    #                 action_str = f"动作是{last_action}。"
    #             else:
    #                 action_str = "没有指定动作。"
    #             continue_message += action_str + "继续你的回答。"
    #         except (json.JSONDecodeError, Exception) as e:
    #             print(f"解析上一次响应失败: {e}")
        
    #     print(f"发送继续消息: {continue_message}")
    #     self.send_message(continue_message)

    # def handle_action_complete(self):
    #     return
    #     """处理动作完成事件"""
    #     print(f"[调试 动作完成事件触发]，waiting_for_action_complete: {self.waiting_for_action_complete}, is_interrupted: {self.is_interrupted}")
    #     print(f"[调试] LLMClient实例ID: {id(self)}")
    #     if self.waiting_for_action_complete and not self.is_interrupted:
    #         print("动作完成后，直接调用send_continue_message")
    #         self.send_continue_message()
    #     self.waiting_for_action_complete = False

    def close(self):
        """停止LLM工作线程并进行清理"""
        print("Closing LLMClient, stopping worker...")
        try:
            # Clear all active requests first
            self._cleanup_all_requests()
            
            # Stop the worker thread
            if hasattr(self, '_worker') and self._worker is not None:
                self._worker.stop()
                print("LLMWorker stopped by LLMClient.close()")
            
        except Exception as e:
            print(f"Error during LLMClient.close(): {e}")
        finally:
            print("LLMClient.close() completed")

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

    def reinitialize_for_pet_change(self):
        """切换桌宠时重新初始化LLM设定"""
        try:
            print(f"LLM模块重新初始化 - 当前桌宠: {settings.petname}")
            # 清除所有活跃请求和待处理消息
            self._cleanup_all_requests()
            # 重新加载配置，包括新桌宠的prompt
            self._load_config()
            # 重置对话历史
            self.reset_conversation()
            print("LLM模块重新初始化完成")
        except Exception as e:
            print(f"LLM模块重新初始化失败: {e}")

    def update_prompt_and_history(self):
        """更新动作列表（当好感度等级变化或动作解锁时调用）"""
        try:
            print(f"[LLM Client] 更新 prompt 和对话历史")
            # 更新动作列表
            self._update_system_prompt()
            # 更新对话历史中的系统消息
            if self.conversation_history and self.conversation_history[0]["role"] == "system":
                self.conversation_history[0]["content"] = self.structured_system_prompt
        except Exception as e:
            print(f"[LLM Client] 更新 prompt 和对话历史失败: {e}")

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

    def _cleanup_all_requests(self):
        """清理所有活跃请求"""
        if hasattr(self, '_active_requests'):
            self._active_requests.clear()

    def _cleanup_request(self, request_id: str):
        """清理请求ID和相关的待处理消息"""
        if hasattr(self, '_active_requests') and request_id in self._active_requests:
            del self._active_requests[request_id]
