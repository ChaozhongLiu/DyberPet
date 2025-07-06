import time
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum
from PySide6.QtCore import QObject, QTimer, Signal
from .. import settings
from .llm_client import LLMClient
import DyberPet.settings as settings

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
        self.llm_client.structured_response_ready.connect(self.handle_structured_response)
        self.llm_client.error_occurred.connect(self.handle_llm_error)

        # 优先级阈值，当累积优先级超过此值时触发请求
        self.priority_threshold = 4
        
        # 空闲检测计时器
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.check_idle_status)
        self.idle_timer.start(15 * 60 * 1000)  # 15分钟检查一次
        
        # 最后一次用户交互时间
        self.last_user_interaction_time = time.time()
        
        # 节流系统 | 记录请求中的事件 & 队列中的事件
        self.requesting_events = {} # request_id: {event_type, event_priority, context， retry_count}
        self.pending_events = {} # (event_type, is_high_priority): {context_list, merge_deadline}
        self.throttle_timer = {}  # 用于高优先级事件的节流倒计时
        
        self.high_priority_throttle_window = 2.0 # 高优先级事件节流窗口（秒）
        self.max_error_retries = settings.llm_config.get('max_retries', 3)    # 最大重试次数（固定为3次）
        self.retry_delay = settings.llm_config.get('retry_delay', 1)    # 重试延迟（秒）

        # 重试定时器管理
        self.retry_timers = {}  # request_id: QTimer

    def _process_high_priority_event(self, event_type: EventType, context_list: List[Dict[str, Any]]):
        """处理高优先级事件，返回请求ID"""
        # 生成请求ID
        request_id = str(uuid.uuid4())

        # Logging
        print(f"处理高优先级事件 {request_id}: {event_type.value}")

        # Build the request message
        message = self.build_request_message(
            {
            event_type: [
                {
                "type": event_type,
                "priority": EventPriority.HIGH,
                "context": context,
                "timestamp": time.time(),
                }
                for context in context_list
            ]
            }
        )
        # 发送请求
        success = self.send_llm_request(message, request_id)

        if success:
            print(f"[LLM Request Manager] 发送高优先级请求成功: {request_id}")
            # Record the event in requesting_events
            self.requesting_events[request_id] = {
                "event_type": event_type,
                "priority": EventPriority.HIGH,
                "message": message,
                "retry_count": 0
            }

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
        self.add_event(event_type, priority, event_data, skip_throttle=True)

    def add_event(self, event_type: EventType, priority: EventPriority, context: Dict[str, Any], skip_throttle=False) -> None:
        """添加事件到累积器"""
        if not settings.llm_config.get('enabled', False):
            print("[LLM Request Manager] LLM未启用，不添加事件")
            return
        
        # 记录当前时间
        current_time = time.time()
        
        # 更新用户交互时间
        if event_type == EventType.USER_INTERACTION:
            self.last_user_interaction_time = current_time
        
        # 高优先级事件直接处理
        if priority == EventPriority.HIGH:
            self.process_high_priority_event(event_type, context, skip_throttle)
            return
        
        # 其他事件加入累积器
        event_data = {
            "type": event_type,
            "priority": priority,
            "context": context,
            "timestamp": current_time
        }
        self.pending_events.setdefault((event_type, False), {'events':[], 'merge_deadline':None})['events'].append(event_data)
        self.check_priority_threshold(event_type)
    
    def process_high_priority_event(self, event_type: EventType, context: Dict[str, Any], skip_throttle=False) -> None:
        """处理高优先级事件，按事件类型合并节流"""
        current_time = time.time()

        if not skip_throttle:

            # Check if there is an existing pending event of the same type
            if self.pending_events.get((event_type, True), {'events': []})['events']:

                # 如果在合并窗口内，更新事件内容
                merge_deadline = self.pending_events[(event_type, True)]["merge_deadline"]
                if current_time <= merge_deadline:
                    # 合并事件到现有事件中
                    self.pending_events[(event_type, True)]["events"].append(context)
                    print(f"[节流] 合并同类型事件: {event_type.value}, 当前时间: {current_time}, 合并截止时间: {merge_deadline}")
                    # 重制节流倒计时
                    self.throttle_timer[(event_type, True)] = QTimer(self)
                    self.throttle_timer[(event_type, True)].setSingleShot(True)
                    self.throttle_timer[(event_type, True)].timeout.connect(
                        lambda et=event_type: self._process_throttle_events((et, True))
                    )
                    self.throttle_timer[(event_type, True)].start(self.high_priority_throttle_window * 1000)
                    return
                else:
                    # 超过合并窗口，处理旧事件
                    print(f"[节流] 处理过期事件: {event_type.value}")
                    pending_events_list = self.pending_events[(event_type, True)]["events"]
                    self.pending_events[(event_type, True)]["events"] = []  # 清空旧事件
                    self._process_high_priority_event(event_type, pending_events_list)

            # 如果该高优先级事件类型正在处理，创建待合并事件
            if event_type in [i['event_type'] for i in self.requesting_events.values() if i['priority'] == EventPriority.HIGH]:
                self.pending_events[(event_type, True)] = {
                    "events": [context],
                    "merge_deadline": current_time + self.high_priority_throttle_window
                }
                print(f"[节流] 创建待合并事件: {event_type.value}, 当前时间: {current_time}, 合并截止时间: {self.pending_events[(event_type, True)]['merge_deadline']}")
                # 设置节流倒计时
                self.throttle_timer[(event_type, True)] = QTimer(self)
                self.throttle_timer[(event_type, True)].setSingleShot(True)
                self.throttle_timer[(event_type, True)].timeout.connect(
                    lambda et=event_type: self._process_throttle_events((et, True))
                )
                self.throttle_timer[(event_type, True)].start(self.high_priority_throttle_window * 1000)
                
                return

            else:
                # 没有待合并事件，直接处理当前事件
                print(f"[节流] 直接处理事件: {event_type.value}")
                self._process_high_priority_event(event_type, [context])
        
        else:
            # 跳过节流，直接处理事件
            print(f"[节流] 跳过节流，直接处理事件: {event_type.value}")
            self._process_high_priority_event(event_type, [context])

    def _process_throttle_events(self, event_key) -> None:
        """处理节流事件"""
        event_type, is_high_priority = event_key
        print(f"[节流] 处理事件: {event_type.value}, 高优先级: {is_high_priority}")

        # 检查是否有待处理的高优先级事件
        if (event_type, is_high_priority) in self.pending_events:
            pending_events_list = self.pending_events[(event_type, is_high_priority)]["events"]
            if pending_events_list:
                print(f"[节流] 发送高优先级请求: {event_type.value}, 事件数量: {len(pending_events_list)}")
                self._process_high_priority_event(event_type, pending_events_list)
                # 清空待合并事件
                self.pending_events[(event_type, is_high_priority)]["events"] = []
            else:
                print(f"[节流] 没有待处理的事件: {event_type.value}")
        
        # 清理节流计时器
        if (event_type, is_high_priority) in self.throttle_timer:
            del self.throttle_timer[(event_type, is_high_priority)]

    def handle_llm_error(self, error_message, request_id: Optional[str] = None):
        """处理LLM错误"""
        print(f"LLM请求错误: {error_message}, 请求ID: {request_id}")

        # 检查请求ID是否存在于当前活跃请求中
        if request_id and request_id not in self.requesting_events:
            print(f"[LLM Request Manager] 忽略未知请求ID的错误: {request_id}")
            return

        # Retry the request
        if self.requesting_events[request_id]["retry_count"] < self.max_error_retries:
            self.requesting_events[request_id]["retry_count"] += 1
            retry_count = self.requesting_events[request_id]["retry_count"]
            print(f"正在重试请求: {request_id}, 重试次数: {retry_count}")
            # 使用定时器添加重试延迟
            retry_timer = QTimer(self)
            retry_timer.setSingleShot(True)
            retry_timer.timeout.connect(lambda: self._retry_request(request_id))
            self.retry_timers[request_id] = retry_timer
            retry_timer.start(self.retry_delay * 1000)  # 转换为毫秒
            return

        else:
            print(f"重试次数过多，停止所有队列并清理请求: {request_id}")
            # 重试失败后停止所有队列
            self._stop_all_queues()
            # 清理失败的请求记录
            self.delete_request(request_id)
            self.error_occurred.emit(error_message) #TODO: 多语言情况下会只返回中文


    def _retry_request(self, request_id: str):
        """执行重试请求"""
        if request_id not in self.requesting_events:
            print(f"重试时请求 {request_id} 已不存在")
            return

        print(f"执行延迟重试: {request_id}")
        # 重新发送请求
        success = self.send_llm_request(self.requesting_events[request_id]["message"], request_id)
        if not success:
            print(f"重试发送失败: {request_id}")
            # 如果发送失败，直接触发错误处理
            self.handle_llm_error("重试发送失败", request_id)

        # 清理重试定时器
        if request_id in self.retry_timers:
            del self.retry_timers[request_id]

    def _stop_all_queues(self):
        """停止所有队列和定时器"""
        print("[LLM Request Manager] 停止所有队列")

        # 停止所有重试定时器
        for timer in self.retry_timers.values():
            if timer.isActive():
                timer.stop()
        self.retry_timers.clear()

        # 停止所有节流定时器
        for timer in self.throttle_timer.values():
            if timer.isActive():
                timer.stop()
        self.throttle_timer.clear()

        # 清理所有待处理事件
        self.pending_events.clear()

        # 清理所有请求中的事件
        self.requesting_events.clear()

        print("[LLM Request Manager] 所有队列已停止")

    def delete_request(self, request_id: Optional[str] = None):
        """清理请求记录"""
        print(f"[LLM Request Manager] 清理请求: {request_id}")

        # 清理重试定时器
        if request_id and request_id in self.retry_timers:
            if self.retry_timers[request_id].isActive():
                self.retry_timers[request_id].stop()
            del self.retry_timers[request_id]

        # 如果没有提供请求ID，直接清理所有活跃请求
        if not request_id:
            print("[LLM Request Manager] 清理所有活跃请求")
            # 清理所有重试定时器
            for timer in self.retry_timers.values():
                if timer.isActive():
                    timer.stop()
            self.retry_timers.clear()
            self.requesting_events.clear()

        # 如果提供了请求ID，清理特定请求
        elif request_id in self.requesting_events:
            print(f"[LLM Request Manager] 清理请求: {request_id}")
            del self.requesting_events[request_id]


    def handle_structured_response(self, response, request_id: Optional[str] = None):
        """处理LLM结构化响应"""
        print(f"[LLM Request Manager] 处理回复: {request_id}")
        
        # 检查请求ID是否存在于当前活跃请求中
        if request_id and request_id not in self.requesting_events:
            print(f"[LLM Request Manager] 忽略未知请求ID的回复: {request_id}")
            return
        
        # 处理响应信号
        self.handle_llm_response(response)
        # 删除请求记录
        self.delete_request(request_id)


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
        events = self.pending_events.get((event_type, False), {}).get('events', [])
        if not events:
            return
        
        # 计算累积优先级
        accumulated_priority = sum(event["priority"].value for event in events)
        print(f"[调试]事件: {events}，优先级: {accumulated_priority}")
        # 检查是否超过阈值
        if accumulated_priority >= self.priority_threshold:
            # 处理累积的事件
            self.process_accumulated_events(event_type)

    
    def process_accumulated_events(self, event_type: EventType) -> None:
        """
        处理指定类型的累积事件
        
        Args:
            event_type: 事件类型
        """
        events = self.pending_events.get((event_type, False), {}).get('events', [])
        if not events:
            return

        # 如果优先级未超阈值，则不处理
        accumulated_priority = sum(event["priority"].value for event in events)
        if ( 
            accumulated_priority < self.priority_threshold):
            return
        
        # Request ID
        request_id = str(uuid.uuid4())

        # Build the request message
        request_message = self.build_request_message({event_type: events})
        # Send the request to LLM
        success = self.send_llm_request(request_message, request_id)

        if success:
            print(f"[LLM Request Manager] 发送请求成功: {request_id}, 事件类型: {event_type.value}")
            # Record the event in requesting_events
            self.requesting_events[request_id] = {
                "event_type": event_type,
                "priority": EventPriority.MEDIUM,
                "message": request_message,
                "retry_count": 0
            }

        # Clear the event accumulator for this type
        self.pending_events[(event_type, False)] = {'events': [], 'merge_deadline': None}
        

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
            return True
        except Exception as e:
            print(f"发送LLM请求失败: {str(e)}")
            return False
        
    def reinitialize(self):
        """重新初始化LLM设定"""
        self._stop_all_queues()
        self.last_user_interaction_time = time.time()
        self.llm_client.reinitialize_for_pet_change()
        
        print(f"[LLM Request Manager] 重新初始化完成 - 当前宠物: {settings.petname}")




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
