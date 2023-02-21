# 素材开发文档
素材开发文档，是想要在「呆啵宠物」现有功能下，开发新的宠物形象、动作等美术素材，所需要参考的标准和指南。
目前包括两个部分：
- 动画开发：宠物形象、动作
- 物品开发：食物、玩具等道具

[素材编辑器](https://github.com/Marcus-P-114514/DyberPetUtil)正在施工中，将更加便捷的帮助开发者编辑素材和配置文件。

## 动画开发  
### 动画实现过程
动画在两个模块中被调用
- **动画模块**：独立于宠物的主界面运行，不会出现因加载动画而出现程序未响应的情况。用户与宠物交互时，动画模块会暂停等待，优先级处于末位。  
- **交互模块**：用于即时响应用户的各种交互行为，宠物状态变化时的行为。


  
程序启动时，将自动读取位于 ``data/pets.json`` 中的宠物列表  
``data/pets.json`` 举例如下：  
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



### 宠物参数文件
宠物参数文件 ``res/role/PETNAME/pet_conf.json`` 举例如下：  
```
{
  "width": 98,              #所有 PNG 图片的最大宽度
  "height": 98,             #所有 PNG 图片的最大高度
  "scale": 1.0,             #图片显示比例，会影响宠物大小、单位时间移动距离
  
  "refresh": 5,             #动画模块随机显示动作之间的时间间隔，单位为 s
  "interact_speed":0.02,    #交互模块的响应刷新间隔，0.02s 是较为理想的间隔，不需要在素材开发时修改

  "default": "default",     #此处定义了一些必要动作
  "up": "up",               #但目前只有 default、drag、fall 真正用到
  "down": "down",           #其他的只是为以后版本拓展所做的拓展
  "left": "left",           #目前可以全都用 default 动作代替
  "right": "right",
  "drag": "drag",           #用法例："default": "angry"
  "fall": "fall",           #定义 default 动作为 动作参数文件中 名为 "angry" 的动作
  
  #random_act 定义了一系列动作组，用于在动画模块中随机展示，或在右键菜单中选择进行展示
  "random_act": [
    {"name":"站立", "act_list":["default"], "act_prob":1.0, "act_type":[2,0]},
    {"name":"左右行走", "act_list":["left_walk", "right_walk","default"], "act_prob":0.1, "act_type":[3,1]},
    {"name":"生气", "act_list":["angry"], "act_prob":1.0, "act_type":[0,0]},
    {"name":"睡觉", "act_list":["fall_asleep", "sleep"], "act_prob":0.05, "act_type":[1,1]},
    {"name":"on_floor", "act_list":["on_floor"], "act_prob":0, "act_type":[0,10000]}
  ],
  
  #accessory_act 定义了一系列拥有组件的动作，在右键菜单中选择进行展示
  "accessory_act":[
    {"name":"XXX", "act_list":["XXX"], "acc_list":["XXX"], "act_type":[2,1],
    "follow_mouse": true, "above_main":false, "anchor":[145,145]}
  ],
  
  #宠物自定义的物品喜爱度 （特别喜欢 / 一般 / 讨厌）
  "item_favorite": {"薯条"：2.0}, # 物品名称：好感度倍率
  "item_dislike": {"汉堡"：0.5}
}
```

#### 宠物参数
| 名称   | 类型         | 默认值      | 备注                  |
|:-----|:-------------|:----------|:----------------------|
| width | integer | 128 | 如果图片宽度超出了128，请务必提供所有图片的最大宽度 |
| height | integer | 128   | 如果图片高度超出了128，请务必提供所有图片的最大高度 |
| scale | float | 1.0   | 图片显示比例，会影响宠物大小、单位时间移动距离 |
| refresh | float | 5.0   | 单位为秒 |
| interact_speed | float | 0.02   | 单位为秒 |
| gravity | float | 4.0   | 单位 ``interact_speed`` 时间 下落速度增加值，**目前整合进入设置界面，无需再添加该属性** |
| default, up, etc. | str | 无   | 这些必要动作一定要写在文件中，但只有default、drag、fall被调用，其他可全都用 default 动作代替 |
| random_act | list | [ ] |  每一个动作组都是一个dict，包含所有动作的名字、图片、概率、和状态阈值。空列表会让动画模块运行异常，不建议一个动作也不定义 2333 |
| name | str | 无 | 动作组的名字，会显示在右键菜单中以供用户选择。如果没有，则不会在菜单中出现 |
| act_list | str list | 无 | 按定义好的顺序，列出动作的名字 |
| act_type | int list | [2,1] | 动作组的状态阈值，例如 [2,1] 中， 2代表饱食度分级为2时触发概率最大，1代表好感等级要大于等于1才能触发 |
| act_prob | float | 0.2 | 动作组在 **定义的饱食度分级下** 的概率，所有动作组概率之和不必为1，只是一个相对大小，程序会处理一切 |
| hp_interval | int/float | 5   | 每隔 n 分钟，饱食度下降1，**目前归为系统属性，无需在宠物属性内添加** |
| fv_interval | int/float | 1   | 每隔 n 分钟，好感度进行一次变化判定，若 hp>50: +1; 0< hp < 50: +0; hp=0: -1，**目前归为系统属性，无需在宠物属性内添加** |

#### 饱食度分级与动作触发概率
假设一个动作组在其定义的饱食度状态下，概率为 a  

| 动作的定义状态 \ 当前饱食度   | 3   | 2  | 1  | 0 |
|:-----|:-------------|:----------|:----------------------|:----------------------|
| 3（活跃 hp>80）   | a    | a/4   | a/16   | 0 |
| 2（正常 hp>50）  | a/4    | a   | a/4   | 0 |
| 1（饥饿 hp>0）  | 0    | 0   | a   | 0 |
| 0（饿死 hp=0）   | 0    | 0   | 0   | a |
  
  
  
### 动作参数文件
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

#### 动作参数
| 名称   | 类型         | 默认值      | 备注                  |
|:-----|:-------------|:----------|:----------------------|
| images | str | 无 | 将动作帧按顺序排列为 ``images_0.png``, ``images_1.png``, etc. |
| act_num | integer | 1 | 将 ``images_0.png``, ``images_1.png`` 等按顺序执行 N 次 |
| need_move | Boolean | false | 动作是否需要移动 |
| direction | str | None | 移动的方向，可为 left, right, up, down |
| frame_move | float | 10.0 | 单位时间间隔移动距离 |
| frame_refresh | float | 0.5 | 单位为秒 |

### 素材开发流程（建议）
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
  - 动作单元编写成动作组，写入宠物参数文件 ``random_act``
- 如果是新创建的宠物，最后在 ``res/pets.json`` 中添加宠物的名字
- 开始运行，测试调整各项参数
  - 下落加速度是否合适？
  - 动作运行速度是否合适？
  - 动作移动速度是否合适？
  - ......


### 其他
  
  
  
# 物品开发  
## 动画实现过程
