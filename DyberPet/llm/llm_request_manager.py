import time
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum
from PySide6.QtCore import QObject, QTimer, Signal
from .. import settings
from .llm_client import LLMClient

class EventPriority(Enum):
    """事件优先级枚举"""
    LOW = 1      # 低优先级：环境感知、时间触发等
    MEDIUM = 2   # 中优先级：状态变化等
    HIGH = 3     # 高优先级：用户直接交互等

class EventType(Enum):
    """事件类型枚举"""
    USER_INTERACTION = "user_interaction"  # 用户交互
    STATUS_CHANGE = "status_change"        # 状态变化
    TIME_TRIGGER = "time_trigger"          # 时间触发
    RANDOM_EVENT = "random_event"          # 随机事件
    ENVIRONMENT = "environment"            # 环境感知

class LLMRequestManager(QObject):
    """大模型请求管理器"""
    
    # 信号定义
    error_occurred = Signal(str, name='error_occurred')
    update_software_monitor = Signal(float, float, name='update_software_monitor')
    register_bubble = Signal(dict, name='register_bubble')
    add_chatai_response = Signal(str, name='add_chatai_response')
    
    def __init__(self, llm_client,parent=None):
        super().__init__(parent)
        
        # 初始化LLM客户端
        self.llm_client = llm_client
        # 只保留结构化响应信号连接
        self.llm_client.structured_response_ready.connect(self.handle_structured_response)
        self.llm_client.error_occurred.connect(self.handle_llm_error)
        
        # 事件累积器，按事件类型分类存储
        self.event_accumulators = {}
        for event_type in EventType:
            self.event_accumulators[event_type] = []

        # 优先级阈值，当累积优先级超过此值时触发请求
        self.priority_threshold = 4
        
        
        # 时间窗口设置（秒）
        self.time_windows = {
            EventType.STATUS_CHANGE: 300,    # 状态变化 5分钟窗口
            EventType.TIME_TRIGGER: 1200,    # 时间触发 20分钟窗口
            EventType.RANDOM_EVENT: 3000,    # 随机事件 50分钟窗口
            EventType.ENVIRONMENT: 1200      # 环境感知 20分钟窗口
        }
                
        # 空闲检测计时器
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.check_idle_status)
        self.idle_timer.start(15 * 60 * 1000)  # 15分钟检查一次
        
        # 事件处理计时器
        self.event_timers = {}
        for event_type in EventType:
            if event_type != EventType.USER_INTERACTION:  # 用户交互不需要计时器
                timer = QTimer(self)
                timer.timeout.connect(lambda et=event_type: self.process_accumulated_events(et))
                window_time = self.time_windows.get(event_type, 600)
                timer.start(window_time * 1000)
                self.event_timers[event_type] = timer
        
        # 最后一次用户交互时间
        self.last_user_interaction_time = time.time()
        
        # 修改为事件合并机制
        self.processing_event_types = set()  # 跟踪正在处理的事件类型
        self.pending_high_priority_events = {}  # 改为字典，按事件类型存储待合并事件
        self.active_requests = {}  # 跟踪活跃的请求：{request_id: event_type}
        self.throttle_window = 2.0
        self.error_retry_count = 0    # 错误重试计数
        self.max_error_retries = 3    # 最大重试次数

    def _process_high_priority_event(self, event_type: EventType, context: Dict[str, Any]) -> str:
        """处理高优先级事件，返回请求ID"""

        print(f"处理高优先级事件: {event_type.value}, 上下文: {context}")
        self.is_processing = True
        self.processing_event_types.add(event_type)

        # 生成请求ID并记录活跃请求
        request_id = str(uuid.uuid4())
        self.active_requests[request_id] = event_type
        # 构建请求消息
        message = self.build_request_message({event_type: [{
            "type": event_type,
            "priority": EventPriority.HIGH,
            "context": context,
            "timestamp": time.time()
        }]})
        # 发送请求
        self.send_llm_request(message, request_id)
        return request_id

    def add_event_from_petwidget(self, data_dict:dict):
        self.add_event(
            data_dict['event_type'],
            data_dict['priority'],
            data_dict['event_data']
        )

    def add_event_from_chatai(self, message: str) -> None:
        event_data = {"message": message, "description": "用户直接对话", "type": "chat"}
        event_data.update({
            "timestamp": time.time(),
            "pet_status": self.get_pet_status()
        })
        event_type = EventType.USER_INTERACTION
        priority = EventPriority.HIGH
        self.add_event(event_type, priority, event_data)

    def add_event(self, event_type: EventType, priority: EventPriority, context: Dict[str, Any]) -> None:
        """添加事件到累积器"""
        # 记录当前时间
        current_time = time.time()
        
        # 更新用户交互时间
        if event_type == EventType.USER_INTERACTION:
            self.last_user_interaction_time = current_time
        
        # 高优先级事件直接处理
        if priority == EventPriority.HIGH:
            self.process_high_priority_event(event_type, context)
            return
        
        # 其他事件加入累积器
        event_data = {
            "type": event_type,
            "priority": priority,
            "context": context,
            "timestamp": current_time
        }
        self.event_accumulators[event_type].append(event_data)
        # print("[调试]",self.event_accumulators)
        # 检查是否需要立即处理（优先级累积超过阈值）
        self.check_priority_threshold(event_type)
    
    def process_high_priority_event(self, event_type: EventType, context: Dict[str, Any]) -> None:
        """处理高优先级事件，按事件类型合并节流"""
        current_time = time.time()
        event_type_value = event_type.value

        # 检查是否有同类型的待合并事件
        if event_type_value in self.pending_high_priority_events:
            existing_event = self.pending_high_priority_events[event_type_value]

            # 如果在合并窗口内，更新事件内容
            if current_time <= existing_event["merge_deadline"]:
                # 合并事件内容（可以根据需要自定义合并逻辑）
                existing_event["context"].update(context)
                existing_event["timestamp"] = current_time
                print(f"[节流] 合并同类型事件: {event_type_value}")
                return
            else:
                # 超过合并窗口，处理旧事件
                print(f"[节流] 处理过期事件: {event_type_value}")
                del self.pending_high_priority_events[event_type_value]  # 先删除再处理
                self._process_high_priority_event(existing_event["type"], existing_event["context"])

        # 如果该事件类型正在处理，创建待合并事件
        if event_type in self.processing_event_types:
            self.pending_high_priority_events[event_type_value] = {
                "type": event_type,
                "context": context.copy(),
                "timestamp": current_time,
                "merge_deadline": current_time + self.throttle_window
            }
            print(f"[节流] 创建待合并事件: {event_type_value}")
            return

        # 检查是否有待合并事件需要一起处理
        if event_type_value in self.pending_high_priority_events:
            # 有待合并事件，合并后一起处理
            pending_event = self.pending_high_priority_events[event_type_value]
            # 合并当前事件到待合并事件中
            pending_event["context"].update(context)
            pending_event["timestamp"] = current_time
            print(f"[节流] 合并当前事件到待合并事件并处理: {event_type_value}")
            # 删除待合并事件并处理合并后的结果
            del self.pending_high_priority_events[event_type_value]
            self._process_high_priority_event(pending_event["type"], pending_event["context"])
        else:
            # 没有待合并事件，直接处理当前事件
            print(f"[节流] 直接处理事件: {event_type_value}")
            self._process_high_priority_event(event_type, context)

    def handle_llm_error(self, error_message, request_id: Optional[str] = None):
        """处理LLM错误"""
        print(f"LLM请求错误: {error_message}, 请求ID: {request_id}")

        # 清理失败的请求记录
        failed_event_type = None
        if request_id and request_id in self.active_requests:
            failed_event_type = self.active_requests[request_id]
            del self.active_requests[request_id]
            self.processing_event_types.discard(failed_event_type)
            print(f"[节流] 清理失败请求: {request_id}, 事件类型: {failed_event_type.value}")

        # 更新全局处理状态
        self.is_processing = len(self.processing_event_types) > 0

        # 尝试重试
        if self.error_retry_count < self.max_error_retries:
            self.error_retry_count += 1

            # 如果有失败的事件类型，优先重试该类型的待合并事件
            if failed_event_type and failed_event_type.value in self.pending_high_priority_events:
                event_data = self.pending_high_priority_events[failed_event_type.value]
                print(f"[节流] 错误重试失败事件类型: {failed_event_type.value} (重试次数: {self.error_retry_count})")
                # 删除待合并事件并重试
                del self.pending_high_priority_events[failed_event_type.value]
                self._process_high_priority_event(event_data["type"], event_data["context"])
            elif self.pending_high_priority_events:
                # 重试第一个待合并事件
                event_type_value = next(iter(self.pending_high_priority_events))
                event_data = self.pending_high_priority_events[event_type_value]
                print(f"[节流] 错误重试处理事件: {event_type_value} (重试次数: {self.error_retry_count})")
                # 删除待合并事件并重试
                del self.pending_high_priority_events[event_type_value]
                self._process_high_priority_event(event_data["type"], event_data["context"])
            else:
                # 没有待处理事件，重置错误计数
                self.error_retry_count = 0
        else:
            # 重试次数过多，清空待合并事件避免卡死
            self.error_retry_count = 0
            self.pending_high_priority_events.clear()
            self.active_requests.clear()  # 同时清空活跃请求记录
            print(f"[节流] 重试次数过多，清空所有待合并事件和活跃请求")
            # Send it to ChatAI
            self.error_occurred.emit(error_message)

    def handle_structured_response(self, response, request_id: Optional[str] = None):
        """处理LLM结构化响应"""
        print(f"[调试 handle_structured_response] 函数触发, 请求ID: {request_id}")
        self.error_retry_count = 0  # 重置错误计数
        # 清理完成的请求记录
        if request_id and request_id in self.active_requests:
            completed_event_type = self.active_requests[request_id]
            del self.active_requests[request_id]
            # 移除该事件类型的处理状态
            self.processing_event_types.discard(completed_event_type)
            print(f"[节流] 请求完成: {request_id}, 事件类型: {completed_event_type.value}")

            # 保留待合并事件，等待下次处理机会
            if completed_event_type.value in self.pending_high_priority_events:
                print(f"[节流] 保留事件类型 {completed_event_type.value} 的待合并事件，等待下次处理")
        else:
            # 如果没有请求ID信息，使用原来的逻辑（向后兼容）
            print(f"[节流] 成功响应，保留所有待合并事件: {list(self.pending_high_priority_events.keys())}")

        # 更新全局处理状态
        self.is_processing = len(self.processing_event_types) > 0

        # 转发结构化响应信号
        self.handle_llm_response(response)

    def handle_llm_response(self, data):
        """
        处理来自LLM的结构化响应
        :param data: 响应数据字典
        """
        # print("[调试 handle_llm_response] 函数触发LLM响应",data)
        if not isinstance(data, dict):
            return
            
        # 处理自适应时间间隔决策
        if data.get('adaptive_timing_decision'):
            new_interval = data.get('recommended_interval')
            new_idle_threshold = data.get('recommended_idle_threshold')
            
            adaptive_interval = None
            if new_interval and isinstance(new_interval, (int, float)) and 300 <= new_interval <= 3600:
                adaptive_interval = new_interval
                print(f"[自适应] 更新交互间隔为 {new_interval} 秒")
            
            idle_threshold = None
            if new_idle_threshold and isinstance(new_idle_threshold, (int, float)) and 60 <= new_idle_threshold <= 1800:
                idle_threshold = new_idle_threshold
                print(f"[自适应] 更新空闲阈值为 {new_idle_threshold} 秒")
            
            self.update_software_monitor.emit(adaptive_interval, idle_threshold)

        # 处理情绪分析结果
        elif data.get('emotion_analysis_result'):
            # ... 处理情绪分析结果的代码 ...
            pass
        
        # 处理任务分析结果
        elif data.get('task_analysis_result'):
            # ... 处理任务分析结果的代码 ...       
            pass 

        # 显示情感气泡 and hasattr(settings, 'bubble_manager') 用于test_llm文件进行测试
        if data.get('emotion') and settings.bubble_on:
            # 获取情感状态并映射到对应图标
            # print("[调试 handle_llm_response] 显示情感气泡")
            emotion = data.get('emotion', 'normal')
            emotion_map = {
                "高兴": "bb_fv_lvlup",
                "难过": "bb_fv_drop",
                "可爱": "bb_hp_low",
                "天使": "bb_hp_zero",
                "正常": "bb_pat_focus",
                "困惑": "bb_pat_frequent",
            }
            emotion_icon = emotion_map.get(emotion, "bb_normal")
            
            # 构造气泡数据
            bubble_data = {
                "bubble_type": "llm",
                "icon": emotion_icon,
                "message": data['text'],
                "countdown": None,
                "start_audio": None,
                "end_audio": None
            }
            
            # 发送气泡
            self.register_bubble.emit(bubble_data)

        # ChatAI 聊天
        if data.get('text'):
            self.add_chatai_response.emit(data['text'])
            # actions_str = data.get('action', '') if isinstance(data.get('action', ''), str) else str(data.get('action', ''))
            # self.chat_history.append(f"<i>执行动作: {actions_str}</i>")

        
        # 执行动作
        if 'action' in data:
            pass
            # self.execute_actions(data['action'])
        
        if 'open_web' in data:
            pass
            # self.open_web(data['open_web'])
        
        #添加代办事项任务
        if 'add_task' in data:
            return
            # TODO: finish the signal connection to Dashboard
            self.board.taskInterface.taskPanel.addTodoCard(data['add_task'])
            
        
    
    def check_priority_threshold(self, event_type: EventType) -> None:
        """检查累积优先级或事件数量是否超过阈值"""
        events = self.event_accumulators[event_type]
        if not events:
            return
        
        # 计算累积优先级
        accumulated_priority = sum(event["priority"].value for event in events)
        print(f"[调试]事件: {events}，优先级: {accumulated_priority}")
        # 检查是否超过阈值
        if accumulated_priority >= self.priority_threshold:
            # 处理累积的事件
            self.process_accumulated_events(event_type)
            # 清空事件累积器
            self.event_accumulators[event_type] = []
    
    def process_accumulated_events(self, event_type: EventType) -> None:
        """
        处理指定类型的累积事件
        
        Args:
            event_type: 事件类型
        """
        events = self.event_accumulators[event_type]
        if not events:
            return
        
        # 检查时间窗口
        current_time = time.time()

        # 如果未到时间窗口结束且优先级未超阈值，则不处理
        accumulated_priority = sum(event["priority"].value for event in events)
        if ( 
            accumulated_priority < self.priority_threshold):
            return
         
        # 构建合并的请求内容
        request_message = self.build_request_message({event_type: events})
        # 生成请求ID并记录
        request_id = str(uuid.uuid4())
        self.active_requests[request_id] = event_type

        # 标记该事件类型正在处理
        self.processing_event_types.add(event_type)
        self.is_processing = True  # 更新全局状态

        # 发送请求
        self.send_llm_request(request_message, request_id)
        # 清空累积器
        self.event_accumulators[event_type] = []
        

    def get_pet_status(self) -> Dict[str, Any]:
        return {
            'pet_name': settings.petname,
            'hp': settings.pet_data.hp,
            'fv': settings.pet_data.fv,
            'hp_tier': settings.pet_data.hp_tier,
            'fv_lvl': settings.pet_data.fv_lvl,
            'time': time.strftime("%H:%M")
        }
    
    def build_request_message(self, events_by_type: Dict[EventType, List[Dict]]) -> str:
        """
        根据累积的事件构建请求消息
        
        Args:
            events_by_type: 按类型分组的事件列表
            
        Returns:
            构建好的请求消息
        """
        try:
            message = ""
            
            # 从事件上下文中获取宠物状态
            pet_status = None
            for events in events_by_type.values():
                for event in events:
                    if isinstance(event, dict) and "context" in event:
                        context = event["context"]
                        if "pet_status" in context:
                            pet_status = context["pet_status"]
                            break
                if pet_status:
                    break
            
            # 如果事件中没有状态信息，则尝试从pet_widget获取
            if not pet_status:
                print("使用默认宠物状态")
                pet_status = self.get_pet_status()
            
            # 添加事件信息
            for event_type, events in events_by_type.items():
                if events:
                    message += f"[{event_type.value}事件]\n"
                    for event in events:
                        if isinstance(event, dict) and "context" in event:
                            context = event["context"]
                            
                            # 根据事件类型格式化上下文
                            if event_type == EventType.USER_INTERACTION:
                                # 检查是否有直接对话消息
                                if "message" in context:
                                    
                                    # 如果有交互强度信息，添加到消息中
                                    if "intensity" in context:
                                        message += f"{context['message']}\n"
                                    else:
                                        message += f"用户说: {context['message']}\n"
                                else:
                                    message += f"{context.get('description')}\n"
                                    # 如果有交互强度信息，添加到消息中
                                    if "intensity" in context:
                                        action_text = context.get('action', '与你互动')
                                        message += f"用户{action_text}\n"
                                        message += f"交互强度: {context['intensity']}\n"
                                    
                            elif event_type == EventType.STATUS_CHANGE:
                                # 提供更多原始信息，减少解释性描述
                                if "event_source" in context:
                                    message += f"来源=>{context['event_source']}\n "
                                message += f"{context.get('description')}\n"
                            elif event_type == EventType.TIME_TRIGGER:
                                message += f"当前是{context.get('time_period', '')}\n"
                            elif event_type == EventType.ENVIRONMENT:
                                message += f"{context.get('description', '')}\n"
                            elif event_type == EventType.RANDOM_EVENT:
                                message += f"随机事件: {context.get('description', '')}\n"
            message += "\n"
            
            # 构建状态消息
            status_message = f"[宠物状态] 名称:{pet_status.get('pet_name', settings.petname)}, "
            status_message += f"hp:{pet_status.get('hp', 0)}/100, "
            status_message += f"好感度:{pet_status.get('fv', 0)}/120, "
            status_message += f"好感度等级:{pet_status.get('fv_lvl', 0)}, "
            status_message += f"时间:{pet_status.get('time', time.strftime('%H:%M'))}"
 
            # 如果有位置信息，添加到状态中
            if 'position' in pet_status:
                pos = pet_status['position']
                status_message += f", 你的位置:({pos['x']}/{pos['screen_width']},{pos['y']}/{pos['screen_height']})"
            
            # 将状态信息添加到消息末尾
            if message:
                message += "\n"
            message += status_message
            
            return message
        except Exception as e:
            print(f"构建请求消息失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""

    def check_idle_status(self) -> None:
        """
        检查空闲状态并触发相应事件
        """
        try:
            current_time = time.time()
            # 检查是否超过空闲时间阈值（15分钟）
            if current_time - self.last_user_interaction_time > 15 * 60:
                # 触发空闲事件
                self.add_event(
                    EventType.TIME_TRIGGER,
                    EventPriority.LOW,
                    {"time_period": "空闲时间", "duration": "15分钟"}
                )
                # 重置计时器
                self.last_user_interaction_time = current_time
        except Exception as e:
            print(f"检查空闲状态失败: {str(e)}")

    def send_llm_request(self, message: str, request_id: Optional[str] = None) -> None:
        """
        发送LLM请求
        Args:
            message: 请求消息内容
            request_id: 请求ID，用于跟踪响应
        """
        try:
            print(f"\n===== 发送LLM请求 (ID: {request_id}) =====\n{message}")
            # 调用LLM客户端发送消息
            self.llm_client.send_message(message, request_id)
        except Exception as e:
            print(f"发送LLM请求失败: {str(e)}")
            # 重置处理状态
            # 清理失败的请求记录
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]


if __name__ == "__main__":
    # 为了测试，直接导入
    import sys
    sys.path.append("c:\\Users\\admint\\Desktop\\新建文件夹\\DyberPet")
    from DyberPet.llm.llm_client import LLMClient
    
    manager = LLMRequestManager()
    context = {"action": "点击宠物"}
    manager.add_event(
        EventType.USER_INTERACTION,
        EventPriority.HIGH,
        context
    )
