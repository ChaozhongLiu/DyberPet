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
#### 1. LLM Request Manager  
- ~~1.1 对于 HIGH 优先级的事件是否需要节流？~~ 需要  
- ~~1.2 self.is_processing 是否真的需要，且目前逻辑混乱~~ 已删除  
- ~~1.3 handle_llm_error() 需要重构。目前仅服务于队列 HIGH 优先级事件，其他优先级并没有重试功能；
        且逻辑有问题，重试也不一定是对产生错误的 request 的重试~~  
- ~~1.4 self.pending_high_priority_events 的后续处理逻辑有误。~~
        ~~目前队列处理依赖于 handle_structured_response() 被信号触发，存在一直堆积的可能；~~ 
        ~~handle_structured_response() 也不应该负责处理堆积的事件~~  
- 1.5 process_accumulated_events() 的逻辑需要优化。当前是把所有事件直接串联构建 message 进行一次请求，
        会把所有事件混在一起，做一次回复，没有道理  
- 1.6 build_request_message() 获取宠物状态逻辑有误。当前会获取堆积事件中最早的一个有状态记录的事件  
- 1.7 build_request_message() 的构建逻辑需要优化。  
        例如，message 需要手动判定是用户信息还是点击力度信息，不利于代码维护和功能更新 
- 1.8 Event 数据的构建分散在 PetWidget 和 LLMRequestManager 各处，且数据的 schema 不统一  
        存在重复添加时间戳和宠物状态等问题；  
        需要将 Event 数据构建集中在 LLMRequestManager 的一个函数中进行，统一数据 schema  
- 1.9 check_idle_status() 逻辑有误。  
        空闲时间事件被创建后，由于是 LOW 优先级，会被加入队列无法触发  
- 1.10 随机事件也没有被实际实现  
- ~~1.11 需要与系统语言选择关联，自动选择 promt 语言~~  
- ~~1.12 切换桌宠后需要初始化所有设定~~  
- ~~1.13 在 LLMRequestManager 内部添加开关~~  
- ~~1.14 重试添加 delay~~  
- ~~1.15 重试失败后应停止所有队列~~  
- 1.16 错误信息支持多语言
- 1.17 与用户行为无关的错误信息不应该返回至 ChatAI 显示，除非产生了需要清除所有队列无法运行 LLMClient 的错误
- 1.18 隐藏启动后首次调整软件监控参数的回复
    
  
#### 2. LLM Client  
- 2.1 self.conversation_history 需要优化；当前会累积所有的历史消息，导致 token 消耗快速增加  
- ~~2.2 清理对齐 settings 和 LLMClient 中所有的 config~~  
- ~~2.3 删除 LLMClient 非结构化输出相关的代码，该功能已不再支持~~  
- ~~2.4 LLMClient.structured_system_prompt 与系统语言关联~~  
- 2.5 LLMClient.structured_system_prompt 动作指令相关的 prompt 需要改进，当前是写死的  
- 2.6 (低优先级) 重构关于 API 选择部分的代码，创立每个 API 的 class，方便功能更新和 API 切换  
        而不是当前到处 if else  
- 2.7 (低优先级) LLMClient._handle_response() 中关于 token 的数据可以发送到设置界面进行 token 消耗的统计  
- ~~2.8 关于多次 response 的动作指令，需要删除并~~ 重新设计如何实现  
- ~~2.9 将几个 update 各种属性的函数与设置界面相连~~  
- ~~2.10 切换桌宠后需要初始化所有设定~~  
- 2.11 需要与对用户的称呼相挂钩  
- ~~2.12 未成功结构化的 response 处理，不能直接发给用户，应返回重试~~  
- ~~2.13 _handle_response() 函数改的逻辑清晰一些~~  
- ~~2.14 出错的请求返回重试，应从 conversation_history 中删除~~
- 2.15 现在的 temperature 和 max token 是否合适？
- 2.16 动态更新 system prompt，可以把宠物状态等信息放进去，节省 token
- 2.17 打开 chatAI 界面聊天时，不需要显示气泡
  
  
#### 3. ChatAI 界面  
- 3.1 切换宠物后需要初始化界面
- 3.2 将错误信息显示在聊天界面居中位置，灰色小字
- 3.3 美化聊天气泡
- 3.4 添加免责声明
- 3.5 保存对话记录功能
- 3.6 添加的回复增加根据 ``<sep>`` 分割回复信息



### LLM 现有相关功能改进计划
1. 软件监控  
    1.1 将 SoftwareMonitor 重构至 LLMRequestManager  
    1.2 为 SoftwareMonitor 设置单独的 Thread 进行任务处理  
    1.3 为软件监控功能添加开关  
2. 动作执行
    - 现在被取消了，需要设计如何使用大模型调用动作
    - PetWidget action_completed 信号会在任何动作完成后被传递，但应该仅限于大模型触发的动作
3. 点击力度大小及llm反馈
    - 点击力度批量处理的逻辑细化
4. 掉落及拖拽事件
5. 数值变化
    - 数值变化的触发逻辑重复？timeout 和 累积到 8
6. 主动聊天


