# 素材开发文档
素材开发指的是想要在「呆啵宠物」现有功能下，开发新的宠物形象、动作等美术素材所需要参考的标准和指南。

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
  
  "random_act": [           #random_act 定义了一系列动作，用于在动画模块中随机展示，或在右键菜单中选择进行展示
    ["default"],
    ["left_walk", "right_walk","default"],
    ["fall_asleep", "sleep"]
  ],
  "act_prob": [0.85,0.1,0.05],                   #在动画模块中，各个动作随机展示的概率，其和可大于1，conf.py 会处理好一切 xD
  "random_act_name": ["站立","左右行走","睡觉"]    #random_act 中定义动作的名称，用于在右键菜单中显示，以供用户选择
}
```



## 动作参数文件
动作参数文件``res/role/PETNAME/act_conf.json``举例如下：
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
}
```



## 素材设计的注意事项




## 其他


