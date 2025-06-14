# 呆啵宠物-LLM 开发中版本

  
## 配置开发环境

### Windows
  建议首先在本地创建新的 **conda** 环境  
  ```
  conda create --name Dyber_pyside python=3.9.18
  conda activate Dyber_pyside
  conda install -c conda-forge apscheduler
  conda install -c conda-forge pynput
  pip install PySide6-Fluent-Widgets==1.5.4 -i https://pypi.org/simple/
  pip install pyside6==6.5.2
  pip install tendo
  conda install requests
  pip install psutil
  pip install dashscope
  ```

  
### MacOS
  建议首先在本地创建新的 **conda** 环境  
  ```
  conda create --name Dyber_pyside python=3.9.18
  conda activate Dyber_pyside
  conda install -c conda-forge apscheduler
  pip install pynput==1.7.6
  pip install PySide6-Fluent-Widgets==1.5.4 -i https://pypi.org/simple/
  pip install pyside6==6.5.2
  pip install tendo
  conda install requests
  pip install psutil
  pip install dashscope
  ```
  

## 开发任务与进度 

### LLM 相关代码框架改进计划
1. LLM Request Manager  
    1.1 对于 HIGH 优先级的事件是否需要节流？  
    1.2 self.is_processing 是否真的需要，且目前逻辑混乱  
    1.3 handle_llm_error() 需要重构。目前仅服务于队列 HIGH 优先级事件，其他优先级并没有重试功能；
        且逻辑有问题，重试也不一定是对产生错误的 request 的重试  
    1.4 self.pending_high_priority_events 的后续处理逻辑有误。
        目前队列处理依赖于 handle_structured_response() 被信号触发，存在一直堆积的可能； 
        handle_structured_response() 也不应该负责处理堆积的事件  
    1.5 process_accumulated_events() 的逻辑需要优化。当前是把所有事件直接串联构建 message 进行一次请求，
        会把所有事件混在一起，做一次回复，没有道理  
    1.6 build_request_message() 获取宠物状态逻辑有误。当前会获取堆积事件中最早的一个有状态记录的事件  
    1.7 build_request_message() 的构建逻辑需要优化。  
        例如，message 需要手动判定是用户信息还是点击力度信息，不利于代码维护和功能更新 
        各种 event 被同时构建成一个 request 也没有道理  
    1.8 Event 数据的构建分散在 PetWidget 和 LLMRequestManager 各处，且数据的 schema 不统一  
        需要将 Event 数据构建集中在 LLMRequestManager 的一个函数中进行，统一数据 schema  
    1.9 check_idle_status() 逻辑有误。  
        空闲时间事件被创建后，由于是 LOW 优先级，会被加入队列无法触发  
        空闲时间事件并没有被实际实现？  
    1.10 随机事件也没有被实际实现  
    1.11 需要与系统语言选择关联，自动选择 promt 语言  
    1.12 切换桌宠后需要初始化所有设定  
    
  
2. LLM Client  
  
  
3. ChatAI 界面  



### LLM 现有相关功能改进计划
1. 软件监控  
    1.1 将 SoftwareMonitor 重构至 LLMRequestManager  
    1.2 为 SoftwareMonitor 设置单独的 Thread 进行任务处理  
    1.3 为软件监控功能添加开关  
2. 动作执行
    - 现在被取消了，需要设计如何使用大模型调用动作
    - PetWidget action_completed 信号会在任何动作完成后被传递，但应该仅限于大模型触发的动作
3. 点击力度大小及llm反馈
    - 点击力度批量处理逻辑
    
4. 掉落及拖拽事件
5. 数值变化
    - 数值变化的触发逻辑重复？timeout 和 累积到8
6. 主动聊天


PetWidget.trigger_event 及其他部分重复添加时间戳和宠物状态
状态字典在不同class里定义和信息有差别
累计事件会一股脑全都合在一起请求 LLM，但很非 High Priority 事件 (如状态变化) 也需要及时回应
设置中显示 token 累计
