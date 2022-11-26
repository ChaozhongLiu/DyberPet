# 素材开发文档
素材开发文档，是想要在「呆啵宠物」现有功能下，开发新的宠物形象、动作等美术素材，所需要参考的标准和指南。

## 动画实现过程
动画在两个模块中被调用
- **动画模块**：独立于宠物的主界面运行，不会出现因加载动画而出现程序未响应的情况。用户与宠物交互时，动画模块会暂停等待，优先级处于末位。  
- **交互模块**：用于即时响应用户的各种交互行为，宠物状态变化时的行为。


  
程序启动时，将自动读取位于 ``res/pets.json`` 中的宠物列表  
``res/pets.json`` 举例如下：  
```
[
  "Kitty_1",
  "Kitty_2"
]
```
  
之后，主程序开始加载有关宠物的各项参数。以 ``Kitty`` 为例  
主程序将寻找
- 宠物参数文件：``res/role/Kitty/pet_conf.json``
- 动作参数文件：``res/role/Kitty/act_conf.json``  

加载各项参数初始化宠物。  
  
当动作被调用时，如 ``stand`` 动作，程序则会按一定 ``时间间隔``、依次，显示位于 ``res/role/Kitty/action/`` 中所有的 ``stand_*.png`` 图片，以实现 GIF 的效果。顺序为 ``stand_0.png``、``stand_1.png``、``stand_2.png``、......  
  
若动作包含移动，如 ``left_walk`` 动作，程序则会在每次更新图片时，依据 ``移动方向``、``单位时间间隔移动距离``，移动整个宠物。  
  
上述行为中的图片，则是所需开发的动作素材；提及的的时间、距离等，则是素材开发时需要添加在 ``res/role/Kitty/act_conf.json`` 的动作参数。



## 宠物参数文件
宠物参数文件 ``res/role/PETNAME/pet_conf.json`` 举例如下：  
```
{
  "width": 98,              #所有 PNG 图片的最大宽度
  "height": 98,             #所有 PNG 图片的最大高度
  "scale": 1.0,             #图片显示比例，会影响宠物大小、单位时间移动距离
  
  "refresh": 5,             #动画模块随机显示动作之间的时间间隔，单位为 s
  "interact_speed":0.02,    #交互模块的响应刷新间隔，0.02s 是较为理想的间隔，不需要在素材开发时修改
  "gravity": 2.0,           #宠物在屏幕中下落的重力加速度

  "default": "default",     #此处定义了一些必要动作
  "up": "up",               #但目前只有 default、drag、fall 真正用到
  "down": "down",           #其他的只是为以后版本拓展所做的拓展
  "left": "left",           #目前可以全都用 default 动作代替
  "right": "right",
  "drag": "drag",           #用法例："default": "angry"
  "fall": "fall",           #定义 default 动作为 动作参数文件中 名为 "angry" 的动作
  
  "random_act": [           #random_act 定义了一系列动作组，用于在动画模块中随机展示，或在右键菜单中选择进行展示
    ["default"],            #每一个动作组都是一个list，包含了动作单元的名字
    ["left_walk", "right_walk","default"],
    ["fall_asleep", "sleep"]
  ],
  "act_prob": [0.85,0.1,0.05],                   #在动画模块中，各个动作随机展示的概率，其和可大于1，conf.py 会处理好一切 xD
  "random_act_name": ["站立","左右行走","睡觉"],   #random_act 中定义动作的名称，用于在右键菜单中显示，以供用户选择
  
  "hp_interval": 10,        #每隔 n 分钟，健康值下降1，与宠物素材的创建无关，可忽略，或更改数值
  "em_interval": 5          #若健康值低于60，每隔 n 分钟，心情值下降1，同上
}
```

### 宠物参数
| 名称   | 类型         | 默认值      | 备注                  |
|:-----|:-------------|:----------|:----------------------|
| width | integer | 128 | 如果图片宽度超出了128，请务必提供所有图片的最大宽度 |
| height | integer | 128   | 如果图片高度超出了128，请务必提供所有图片的最大高度 |
| scale | float | 1.0   | 图片显示比例，会影响宠物大小、单位时间移动距离 |
| refresh | float | 5.0   | 单位为秒 |
| interact_speed | float | 0.02   | 单位为秒 |
| gravity | float | 4.0   | 单位 ``interact_speed`` 时间 下落速度增加值 |
| default, up, etc. | str | 无   | 这些必要动作一定要写在文件中，但只有default、drag、fall被调用，其他可全都用 default 动作代替 |
| random_act | list | [ ] |  每一个动作组合都是一个list，包含所有动作的名字。每个空列表会让动画模块运行异常，不建议一个动作也不定义 2333 |
| act_prob | float list | 所有动作全都相同概率 | 在动画模块中，各个动作随机展示的概率，其和不必一定等于1，主程序会处理好一切 |
| random_act_name | str list | None | 所有动作组合的名字，会显示在右键菜单中以供用户选择。如果没有，则不会在菜单中出现 |




## 动作参数文件
动作参数文件 ``res/role/PETNAME/act_conf.json`` 举例如下：
```
{
  "default": {               #动作名，对应在宠物参数文件中 "default": -> "default" <-
    "images": "stand",       #PNG 文件前缀，这里指的是所有 stand_0.png, stand_1.png, etc.
    "act_num": 1             #动作次数，所有的 PNG 图片按次序重复展示的次数
  },                         #其他没有定义的参数会在加载时自动取默认数值，stand 动作没有移动效果，不需要其他参数，忽略即可
  
  "right": {                 #这里，定义为 right 的动作仍然是 stand为前缀的所有PNG文件
    "images": "stand",
    "act_num": 1
  },
  "left_walk": {             #left_walk 是用户自己定义的一个需要移动的动作
    "images": "leftwalk",
    "act_num": 5,            #动作次数的定义减轻了图片存储的内存压力，只需载入一个循环，即可做指定次数
                             #比如这里只需要做猫猫前后脚交替的一个循环，即可一直向前移动
                             
    "need_move": true,       #动作是否需要移动，true为需要移动
    "direction": "left",     #移动的方向，可为 left, right, up, down
    "frame_move": 0.5,       #单位时间间隔移动距离
    "frame_refresh": 0.2     #PNG 图片替换的时间间隔，即单帧刷新时间
  }
}                            #可按上述结构任意添加动作，增加到宠物参数文件的 random_act 中
```

### 动作参数
| 名称   | 类型         | 默认值      | 备注                  |
|:-----|:-------------|:----------|:----------------------|
| images | str | 无 | 将动作帧按顺序排列为 ``images_0.png``, ``images_1.png``, etc. |
| act_num | integer | 1 | 将 ``images_0.png``, ``images_1.png`` 等按顺序执行 N 次 |
| need_move | Boolean | false | 动作是否需要移动 |
| direction | str | None | 移动的方向，可为 left, right, up, down |
| frame_move | float | 10.0 | 单位时间间隔移动距离 |
| frame_refresh | float | 0.5 | 单位为秒 |

## 素材开发流程（建议）
- 如果是新创建的宠物
  - 在 ``res/role/`` 中新建文件夹，命名为宠物名字
- 设计所有动作并保存为透明背景的 PNG 图片
  - 所有图片保存在 ``res/role/宠物名字/action`` 中
  - 请保证所有图片中，宠物的绝对大小（所占像素点数）是相同的
  - 所有脚部在地面的图片，请保证地面为图片底部，这是为了让宠物显示在正确的位置。
- 将每个动作单元的文件命名为相同前缀 + ``_*.png``，* 为从0开始的次序
- 在 ``res/role/宠物名字/act_conf.json`` 创建动作参数文件，写入每个动作单元
- 在 ``res/role/宠物名字/pet_conf.json`` 创建宠物参数文件
  - 填写各项参数
  - 动作单元编写成动作组，写入宠物参数文件
    - random_act 填写动作组
    - act_prob 填写概率
    - random_act_name 给动作组命名
- 如果是新创建的宠物，最后在 ``res/pets.json`` 中添加宠物的名字
- 开始运行，测试调整各项参数
  - 下落加速度是否合适？
  - 动作运行速度是否合适？
  - 动作移动速度是否合适？
  - ......


## 其他


