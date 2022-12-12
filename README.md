
# 呆啵宠物  |  DyberPet
[![License](https://img.shields.io/github/license/ChaozhongLiu/DyberPet.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![DyberPet Version](https://img.shields.io/badge/DyberPet-v0.1.7-green.svg)  
呆啵宠物 (DyberPet) 是一个基于 PyQt5 的桌面宠物开发框架，致力于为开发者提供创造桌面宠物的底层功能库。目前项目处于极早期阶段，欢迎各位的加入，一起构建框架 (´･Д･)」




## 快速体验 Demo
### Windows 用户
  将仓库下载至本地，双击 **``run_DyberPet.exe``** 即可

### MacOS 用户
  建议首先在本地创建新的 **conda** 环境  
  ```
  conda create --name DyberPet
  conda activate DyberPet
  conda install -c anaconda pyqt
  conda install -c conda-forge apscheduler
  ```
  将仓库下载至本地，之后运行 **``run_DyberPet.py``** 即可




## 用户手册
请参考用户手册，体验现有功能 (施工中)




## 开发者文档
### 素材开发
若您想要在现有功能下，开发一套新的宠物形象、动作，请参考[素材开发文档](docs/art_dev.md)

### 功能开发
若您想要在现有模块下，开发新的功能，请参考[功能开发文档](README.md) (施工中)


## 更新日志

<details>
  <summary>版本更新列表</summary>
  
**  **
**v0.1.7 - 12/11/2022**
- 添加了计划任务完成后的物品掉落事件

**v0.1.7 - 12/10/2022 (大的来了)**
- 添加了背包系统，可以使用宠物获得的物品（目前只是功能测试阶段，UI极其丑陋，甚至不一致）
  - 在 settings 中增加了 pet_data，用来存储宠物数值和物品的数据
  - 添加了 item_data 和 ``res/items/item_config.json``，用于素材开发中设定物品属性（素材开发文档待更新）
  - 完善了背包交互的一系列可能行为的系统反馈，尽可能考虑了各种情况（可能仍然有bug）
  - 连接了物品使用与数值变化、动画播放
- 添加了通知系统，将取代旧版本中的对话框
  - 定义了 QToaster class 及目前定义的通知类型字段
  - 通知消息会伴随喵叫声
  - 为物品使用和数值变化添加了通知
  - 为计划任务添加了通知，删除了对话框显示（代码仍然在）

**v0.1.6 - 12/03/2022**
- 添加了提醒事项的到时提醒
- 添加了间隔提醒功能
- 关闭宠物后，备忘录会保留
- 添加了对话显示的排队系统，避免冲突

**v0.1.6 - 12/02/2022**
- 添加了专注时间功能
- 添加了番茄时钟和专注时间的倒计时
- 添加了提醒事项（备忘录）
- 该版本下，健康和心情会不断下降，暂时没有和其他功能连接，会在后续版本中添加

**v0.1.5 - 11/27/2022**
- 解决了使用 ``apscheduler`` 时 ``pyinstaller`` 的 bug
- 添加了番茄时间功能

**v0.1.5 - 11/26/2022**
- 采用 ``apscheduler`` 规范化了计划任务模块
- 增加了宠物数值相关数据的读取、修改、存储系统
- 重构了文件夹结构

**v0.1.5 - 11/25/2022**
- 增加了对话框和显示对话的功能
- 增加了计划任务模块
- 计划任务模块增加任务：运行时打招呼、健康和心情随时间下降

**v0.1.4 - 11/23/2022**
- 增加了心情数值
- 更新了呆啵宠物的图标

**v0.1.4 - 11/20/2022**
- 增加了鼠标停留时数值系统的显示 （未实装功能）

**v0.1.3 - 11/19/2022**
- 模块化重构了项目代码

**v0.1.2 - 11/14/2022**
- 最初版本上线


</details>

## 致谢
- Demo 中的部分素材来自 [daywa1kr](https://github.com/daywa1kr/Desktop-Cat)
- 框架早期的动画模块的逻辑参考了 [yanji255](https://toscode.gitee.com/yanji255/desktop_pet/)  
- 框架拖拽掉落的计算逻辑参考了 [WolfChen1996](https://github.com/WolfChen1996/DesktopPet)
- 对话框字体来自 [造字工房](https://www.makefont.com/)，未经允许不可用于商业用途

