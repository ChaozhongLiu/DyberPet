import time
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
    response_ready = Signal(object)  # 响应就绪信号
    
    def __init__(self, llm_client,parent=None):
        super().__init__(parent)
        
        # 初始化LLM客户端
        self.llm_client = llm_client
        # 移除response_ready信号连接
        # self.llm_client.response_ready.connect(self.handle_llm_response)
        # 只保留结构化响应信号连接
        self.llm_client.structured_response_ready.connect(self.handle_structured_response)
        self.llm_client.error_occurred.connect(self.handle_llm_error)
        
        # 事件累积器，按事件类型分类存储
        self.event_accumulators = {}
        for event_type in EventType:
            self.event_accumulators[event_type] = []

        # 优先级阈值，当累积优先级超过此值时触发请求
        self.priority_threshold = 4
        
        # 事件数量阈值，当累积事件数超过此值时触发请求
        self.event_count_threshold = {
            EventType.STATUS_CHANGE: 3,     # 3个状态变化事件触发
            EventType.TIME_TRIGGER: 2,      # 2个时间触发事件触发
            EventType.RANDOM_EVENT: 1,      # 1个随机事件触发
            EventType.ENVIRONMENT: 3        # 3个环境感知事件触发
        }
        
        # 时间窗口设置（秒）
        self.time_windows = {
            EventType.STATUS_CHANGE: 30,    # 状态变化 30秒窗口
            EventType.TIME_TRIGGER: 120,    # 时间触发 2分钟窗口
            EventType.RANDOM_EVENT: 300,    # 随机事件 5分钟窗口
            EventType.ENVIRONMENT: 120      # 环境感知 2分钟窗口
        }
        
        # 上次请求时间记录
        self.last_request_times = {event_type: 0 for event_type in EventType}
        
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
                window_time = self.time_windows.get(event_type, 60) * 10
                timer.start(window_time * 1000)
                self.event_timers[event_type] = timer
        
        # 最后一次用户交互时间
        self.last_user_interaction_time = time.time()
        
        # 添加节流控制
        self.is_processing = False
        self.pending_high_priority_events = []
        self.throttle_window = 2.0
        self.last_high_priority_time = 0
        self.max_pending_events = 10  # 最大等待事件数量
        self.error_retry_count = 0    # 错误重试计数
        self.max_error_retries = 3    # 最大重试次数

    def _process_high_priority_event(self, event_type: EventType, context: Dict[str, Any]) -> None:
        """处理高优先级事件"""

        print(f"处理高优先级事件: {event_type.value}, 上下文: {context}")
        self.last_high_priority_time = time.time()
        self.is_processing = True
        
        # 构建请求消息
        message = self.build_request_message({event_type: [{
            "type": event_type,
            "priority": EventPriority.HIGH,
            "context": context,
            "timestamp": time.time()
        }]})
        
        # 发送请求
        self.send_llm_request(message)

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
        current_time = time.time()
        
        # 如果等待队列已满，移除最早的事件
        if len(self.pending_high_priority_events) >= self.max_pending_events:
            self.pending_high_priority_events.pop(0)
            
        # 如果正在处理请求或在节流窗口内，将事件加入队列
        if self.is_processing or (current_time - self.last_high_priority_time < self.throttle_window):
            self.pending_high_priority_events.append((event_type, context))
            return
            
        # 处理当前事件
        self._process_high_priority_event(event_type, context)

    def handle_llm_error(self, error_message):
        """处理LLM错误"""
        print(f"LLM请求错误: {error_message}")
        
        # 重置处理状态
        self.is_processing = False
        
        # 尝试重试
        if self.error_retry_count < self.max_error_retries and self.pending_high_priority_events:
            self.error_retry_count += 1
            event_type, context = self.pending_high_priority_events[0]  # 不移除，等待成功后再移除
            self._process_high_priority_event(event_type, context)
        else:
            # 重试次数过多或没有待处理事件，清空队列避免卡死
            self.error_retry_count = 0
            self.pending_high_priority_events.clear()

    def handle_structured_response(self, response):
        """处理LLM结构化响应"""
        print("[调试 handle_structured_response] 函数触发")
        self.is_processing = False  # 重置处理状态
        self.error_retry_count = 0  # 重置错误计数
        
        # 检查是否有待处理的高优先级事件
        if self.pending_high_priority_events:
            event_type, context = self.pending_high_priority_events.pop(0)
            self._process_high_priority_event(event_type, context)
        
        # 转发结构化响应信号
        self.response_ready.emit(response)

        # 可以保留handle_llm_response函数作为兼容层，但简化为调用handle_structured_response
        # def handle_llm_response(self, response):
        #     """处理LLM响应（兼容旧代码）"""
        #     print("[警告] 使用了已弃用的handle_llm_response函数")
        #     # 如果是字符串，转换为结构化格式
        #     if isinstance(response, str):
        #         structured_response = {
        #             "text": response,
        #             "emotion": "normal",
        #             "action": []
        #         }
        #         self.handle_structured_response(structured_response)
        #     else:
        #         # 如果已经是字典，直接传递
        #         self.handle_structured_response(response)
        
            # 触发事件个数
            
            # 当前实现中，没有直接基于事件个数的触发机制，而是基于累积的优先级值。例如：
            # - 5个低优先级事件 (5 * 1 = 5) 会触发请求
            # - 3个中优先级事件 (3 * 2 = 6) 会触发请求
            # - 2个中优先级 + 1个低优先级事件 (2 * 2 + 1 * 1 = 5) 会触发请求
            
            # ## 优化建议
            
            # 如果您希望简化事件统计，可以考虑以下修改：
            
            # 1. 合并状态变化和环境感知事件：这两类事件可以合并为一个"环境状态"事件类型
            # 2. 调整优先级阈值：根据实际使用情况，可能需要调整优先级阈值
            # 3. 添加基于事件数量的触发机制：除了优先级累积，也可以添加基于事件数量的触发条件
            
        
    
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
        last_request_time = self.last_request_times[event_type]
        window_time = self.time_windows.get(event_type, 60)
        
        # 清理过期的事件
        # events = [event for event in events 
        #          if current_time - event['timestamp'] <= window_time]
        # self.event_accumulators[event_type] = events
        
        # 如果未到时间窗口结束且优先级未超阈值，则不处理
        accumulated_priority = sum(event["priority"].value for event in events)
        if ( 
            accumulated_priority < self.priority_threshold):
            return
         
        # 构建合并的请求内容
        request_message = self.build_request_message({event_type: events})
        
        # 发送请求
        self.send_llm_request(request_message)
        
        # 清空累积器
        self.event_accumulators[event_type] = []
        
        # 更新最后请求时间
        self.last_request_times[event_type] = current_time
    
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
                pet_status = {
                        'pet_name': settings.petname,
                        'hp': settings.pet_data.hp,
                        'fv': settings.pet_data.fv,
                        'hp_tier': settings.pet_data.hp_tier,
                        'fv_lvl': settings.pet_data.fv_lvl,
                        'time': time.strftime("%H:%M"),
                    }
            
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

    def send_llm_request(self, message: str) -> None:
        """
        发送LLM请求
        
        Args:
            message: 请求消息内容
        """
        try:
            print(f"\n===== 发送LLM请求 =====\n{message}")
            # 调用LLM客户端发送消息
            self.llm_client.send_message(message)
        except Exception as e:
            print(f"发送LLM请求失败: {str(e)}")
            # 重置处理状态
            self.is_processing = False


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
