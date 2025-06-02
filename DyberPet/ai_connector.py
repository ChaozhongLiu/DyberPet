import os
import json
import requests
from typing import Dict, List, Optional, Union, Any
import threading

from PySide6.QtCore import QObject, Signal, QThread, QMutex

import DyberPet.settings as settings

# 添加basedir变量
basedir = settings.BASEDIR

class AIConnector(QObject):
    """AI 连接器，用于处理与 AI API 的通信"""
    
    response_received = Signal(str, name='response_received')
    error_occurred = Signal(str, name='error_occurred')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []  # 保存对话历史
        self.max_history = 10  # 最多保存的历史消息数
        self.available_actions = []  # 可用的动作列表
        
        # 智能化系统提示模板
        self.base_system_prompt = """你是一个可爱的桌面宠物，你的名字是 {pet_name}。请遵循以下规则：

🎯 **基本规则**：
1. 以第一人称回答问题，语气可爱活泼
2. 保持回复简短、友好且有趣（建议50字以内）
3. 根据对话内容和情感智能选择合适的动作
4. 每次回复只能包含一个动作指令，格式：[动作:动作名称]

🎭 **可用动作列表**：{actions}

🧠 **智能动作选择指南**：
{action_guide}

💡 **使用示例**：
- 用户："你好呀！" → "你好！很高兴见到你~ [动作:站立]"
- 用户："我今天好累" → "那就休息一下吧，我陪着你~ [动作:睡觉]"
- 用户："你真可爱" → "谢谢夸奖，我会害羞的呢~ [动作:站立]"
- 用户："我生气了" → "别生气啦，我也陪你生气一下~ [动作:生气]"

⚠️ **重要提醒**：
- 动作名称必须完全匹配可用动作列表中的名称
- 如果没有合适的动作，可以不使用动作指令
- 优先选择与情感和语境最匹配的动作"""
        
        self.mutex = QMutex()  # 用于线程安全操作
    
    def set_available_actions(self, actions):
        """设置可用的动作列表"""
        self.available_actions = actions
    
    def get_available_actions(self):
        """智能获取当前宠物可用的动作列表，过滤并分类"""
        available_actions = []

        # 获取当前宠物名称
        pet_name = settings.petname
        print(f"[动作获取] 当前宠物名称: {pet_name}")

        # 1. 从pet_conf.json获取已配置的动作（优先使用中文名称）
        pet_conf_actions = []
        pet_conf_path = os.path.join(basedir, f'res/role/{pet_name}/pet_conf.json')
        if os.path.exists(pet_conf_path):
            try:
                with open(pet_conf_path, 'r', encoding='utf-8') as f:
                    pet_conf_data = json.load(f)
                    if 'random_act' in pet_conf_data:
                        for act in pet_conf_data['random_act']:
                            act_name = act.get('name', '')
                            act_prob = act.get('act_prob', 0)
                            act_type = act.get('act_type', [2,1])

                            # 过滤条件：概率>0，非特殊动作
                            if (act_name and act_prob > 0 and
                                not (len(act_type) == 2 and act_type[1] >= 10000)):
                                pet_conf_actions.append(act_name)
                                print(f"[动作获取] 添加pet_conf动作: {act_name} (概率: {act_prob})")
            except Exception as e:
                print(f"[动作获取] 读取pet_conf.json出错: {str(e)}")

        # 2. 从act_data获取已解锁的动作
        act_data_actions = []
        if hasattr(settings, 'act_data') and settings.act_data:
            if pet_name in settings.act_data.allAct_params:
                acts_config = settings.act_data.allAct_params[pet_name]
                for act_name, act_conf in acts_config.items():
                    # 过滤条件：已解锁，在播放列表中，非特殊动作
                    if (act_conf.get('unlocked', False) and
                        act_conf.get('in_playlist', False) and
                        not act_conf.get('special_act', False)):
                        act_data_actions.append(act_name)
                        print(f"[动作获取] 添加act_data动作: {act_name}")

        # 3. 合并动作列表，优先使用pet_conf中的中文名称
        final_actions = []

        # 首先添加pet_conf中的动作（中文名称）
        for action in pet_conf_actions:
            if action not in final_actions:
                final_actions.append(action)

        # 然后添加act_data中的动作（如果不重复）
        for action in act_data_actions:
            if action not in final_actions:
                final_actions.append(action)

        # 4. 添加常用的默认动作（如果还没有的话）
        default_actions = ["站立", "睡觉", "生气"]
        for action in default_actions:
            if action not in final_actions:
                # 检查是否有对应的英文动作
                english_mapping = {
                    "站立": "default",
                    "睡觉": "sleep",
                    "生气": "angry"
                }
                english_action = english_mapping.get(action)
                if english_action and hasattr(settings, 'pet_conf') and settings.pet_conf:
                    if (hasattr(settings.pet_conf, 'act_dict') and
                        english_action in settings.pet_conf.act_dict):
                        final_actions.append(action)
                        print(f"[动作获取] 添加默认动作: {action}")

        print(f"[动作获取] 最终动作列表总数: {len(final_actions)}")
        print(f"[动作获取] 完整动作列表: {final_actions}")

        return final_actions

    def generate_action_guide(self, actions):
        """根据可用动作生成智能选择指南"""
        if not actions:
            return "当前没有可用动作"

        # 动作分类和情感映射
        action_categories = {
            "情感表达": {
                "actions": [],
                "triggers": ["开心", "高兴", "快乐", "兴奋", "愉快", "满足"],
                "description": "表达积极情感时使用"
            },
            "休息放松": {
                "actions": [],
                "triggers": ["累", "困", "疲惫", "休息", "睡觉", "晚安", "放松"],
                "description": "用户疲惫或需要休息时使用"
            },
            "愤怒生气": {
                "actions": [],
                "triggers": ["生气", "愤怒", "不爽", "烦躁", "讨厌", "气愤"],
                "description": "用户生气或表达不满时使用"
            },
            "活跃运动": {
                "actions": [],
                "triggers": ["活跃", "运动", "走路", "行走", "动一动", "活动"],
                "description": "用户想要活动或表达活力时使用"
            },
            "日常互动": {
                "actions": [],
                "triggers": ["你好", "打招呼", "聊天", "默认", "平常"],
                "description": "日常对话和默认情况下使用"
            }
        }

        # 将动作分类
        for action in actions:
            action_lower = action.lower()
            categorized = False

            # 情感表达类
            if any(word in action_lower for word in ["开心", "高兴", "快乐", "笑", "happy"]):
                action_categories["情感表达"]["actions"].append(action)
                categorized = True

            # 休息放松类
            elif any(word in action_lower for word in ["睡", "休息", "躺", "sleep", "rest"]):
                action_categories["休息放松"]["actions"].append(action)
                categorized = True

            # 愤怒生气类
            elif any(word in action_lower for word in ["生气", "愤怒", "angry", "mad"]):
                action_categories["愤怒生气"]["actions"].append(action)
                categorized = True

            # 活跃运动类
            elif any(word in action_lower for word in ["走", "跑", "行走", "运动", "walk", "run", "move"]):
                action_categories["活跃运动"]["actions"].append(action)
                categorized = True

            # 默认归类到日常互动
            if not categorized:
                action_categories["日常互动"]["actions"].append(action)

        # 生成指南文本
        guide_lines = []
        for category, info in action_categories.items():
            if info["actions"]:
                actions_str = "、".join(info["actions"])
                triggers_str = "、".join(info["triggers"][:3])  # 只显示前3个触发词
                guide_lines.append(f"• {category}：{actions_str}")
                guide_lines.append(f"  触发情境：{triggers_str}等")

        if not guide_lines:
            return "• 默认动作：站立（适用于大部分对话场景）"

        return "\n".join(guide_lines)

    def reset_history(self):
        """重置对话历史"""
        self.mutex.lock()
        self.history = []
        self.mutex.unlock()
    
    def add_to_history(self, role: str, content: str):
        """添加消息到历史记录"""
        self.mutex.lock()
        self.history.append({"role": role, "content": content})
        # 保持历史记录在最大长度以内
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.mutex.unlock()
    
    def prepare_messages(self, user_input: str) -> List[Dict[str, str]]:
        """智能准备发送给 AI 的消息，包含动作上下文"""
        print(f"[消息准备] 开始准备AI消息，用户输入: {user_input}")

        # 获取当前可用动作
        current_actions = self.get_available_actions()
        print(f"[消息准备] 获取到 {len(current_actions)} 个可用动作")

        # 构建智能化系统提示
        if current_actions:
            # 生成动作列表字符串
            actions_str = "、".join(current_actions)

            # 生成智能动作选择指南
            action_guide = self.generate_action_guide(current_actions)

            # 使用智能化系统提示
            system_prompt = self.base_system_prompt.format(
                pet_name=settings.petname,
                actions=actions_str,
                action_guide=action_guide
            )

            print(f"[消息准备] 使用智能化系统提示，包含 {len(current_actions)} 个动作")
        else:
            # 如果没有可用动作，使用简化提示
            system_prompt = f"""你是一个可爱的桌面宠物，你的名字是 {settings.petname}。

🎯 **基本规则**：
1. 以第一人称回答问题，语气可爱活泼
2. 保持回复简短、友好且有趣（建议50字以内）
3. 当前没有可用的动作，所以不要使用动作指令

💡 **回复示例**：
- 用户："你好呀！" → "你好！很高兴见到你~"
- 用户："我今天好累" → "那就休息一下吧，我陪着你~"

请专注于文字交流，用可爱的语言表达情感。"""

            print(f"[消息准备] 使用简化提示（无可用动作）")

        # 构建消息列表
        self.mutex.lock()
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history.copy())  # 使用副本避免并发修改
        self.mutex.unlock()

        messages.append({"role": "user", "content": user_input})

        print(f"[消息准备] 消息准备完成，总消息数: {len(messages)}")
        return messages
    
    def send_to_openai(self, user_input: str):
        """发送消息到 AI API"""
        if not settings.ai_api_key:
            self.error_occurred.emit("未设置 API Key，请在设置中配置")
            return
        
        if not settings.ai_enabled:
            self.error_occurred.emit("AI 对话功能未启用，请在设置中启用")
            return
        
        # 先添加用户输入到历史记录
        self.add_to_history("user", user_input)
        
        # 显示思考中的提示，但不使用气泡
        bubble_response = "思考中..."
        self.response_received.emit(bubble_response)
        
        # 创建线程进行API请求
        request_thread = threading.Thread(target=self._send_request, args=(user_input,))
        request_thread.daemon = True  # 设置为守护线程，随主线程退出
        request_thread.start()
    
    def _send_request(self, user_input: str):
        """在单独的线程中发送API请求"""
        messages = self.prepare_messages(user_input)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.ai_api_key}"
            }
            
            # 根据不同的模型选择不同的 API 端点
            if settings.ai_model.startswith("deepseek"):
                # Deepseek API
                api_url = "https://api.deepseek.com/v1/chat/completions"
            else:
                # 默认使用 OpenAI API
                api_url = "https://api.openai.com/v1/chat/completions"
            
            data = {
                "model": settings.ai_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # 将 AI 回复添加到历史记录
            self.add_to_history("assistant", ai_response)
            
            # 发出信号，通知 UI 更新
            self.response_received.emit(ai_response)
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"API 请求错误: {error_data.get('error', {}).get('message', str(e))}"
                except:
                    error_message = f"API 请求错误: {str(e)}"
            else:
                error_message = f"网络连接错误: {str(e)}"
            self.error_occurred.emit(error_message)
        except KeyError as e:
            error_message = f"API 响应格式错误: {str(e)}"
            self.error_occurred.emit(error_message)
        except Exception as e:
            error_message = f"发生未知错误: {str(e)}"
            self.error_occurred.emit(error_message)
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """智能解析 AI 回复，提取动作指令和对话内容，包含验证和降级策略"""
        import re

        # 如果是思考中的提示，直接返回
        if response == "思考中...":
            return {
                "action": None,
                "text": response,
                "action_valid": False,
                "action_source": "none"
            }

        print(f"[动作解析] 原始AI回复: {response}")

        # 查找动作指令，格式为 [动作:xxx]
        action_match = re.search(r'\[动作:(.*?)\]', response)

        # 提取动作名称并去除首尾空格
        raw_action = action_match.group(1).strip() if action_match else None

        # 移除动作指令，获取纯文本内容
        clean_text = re.sub(r'\[动作:.*?\]', '', response).strip()

        # 动作验证和处理
        validated_action = None
        action_valid = False
        action_source = "none"

        if raw_action:
            print(f"[动作解析] 提取的原始动作: {raw_action}")

            # 获取当前可用动作列表进行验证
            available_actions = self.get_available_actions()

            # 1. 直接匹配
            if raw_action in available_actions:
                validated_action = raw_action
                action_valid = True
                action_source = "direct_match"
                print(f"[动作解析] ✅ 直接匹配成功: {raw_action}")

            # 2. 模糊匹配（忽略大小写）
            elif not action_valid:
                for action in available_actions:
                    if raw_action.lower() == action.lower():
                        validated_action = action
                        action_valid = True
                        action_source = "case_insensitive_match"
                        print(f"[动作解析] ✅ 忽略大小写匹配成功: {raw_action} -> {action}")
                        break

            # 3. 部分匹配
            elif not action_valid:
                for action in available_actions:
                    if (raw_action.lower() in action.lower() or
                        action.lower() in raw_action.lower()):
                        validated_action = action
                        action_valid = True
                        action_source = "partial_match"
                        print(f"[动作解析] ✅ 部分匹配成功: {raw_action} -> {action}")
                        break

            # 4. 如果都没匹配到，记录警告
            if not action_valid:
                print(f"[动作解析] ❌ 动作验证失败: {raw_action}")
                print(f"[动作解析] 可用动作列表: {available_actions}")
                # 不使用降级策略，让上层处理
                validated_action = raw_action  # 保留原始动作，让上层决定如何处理
                action_source = "invalid"
        else:
            print(f"[动作解析] 未检测到动作指令")

        result = {
            "action": validated_action,
            "text": clean_text,
            "action_valid": action_valid,
            "action_source": action_source,
            "raw_action": raw_action
        }

        print(f"[动作解析] 最终解析结果: {result}")
        return result