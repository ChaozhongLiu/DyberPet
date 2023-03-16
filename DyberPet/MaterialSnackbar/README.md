# Material Snackbar

## 简介

Material Design3风格的Snackbar，参考了Material Design Guideline。



## 使用

- 编译资源和窗体文件

  - ```shell
    pyrcc5 -o "./DyberPet/MaterialSnackbar/resources.py" "./DyberPet/MaterialSnackbar/resources.qrc"
    pyuic5 -o "./DyberPet/MaterialSnackbar/snackBar.py" "./DyberPet/MaterialSnackbar/snackBar.ui"
    ```

- 修改<code>snackBar.py</code>末行的资源路径

  - ```python
    import DyberPet.MaterialSnackbar.resources
    ```

- 配置<code>backend.py</code>中的HDPI支持

  - 如果程序与<code>v.0.2.2</code>的缩放逻辑一致，则请修改：
  - ```python
    overrideHDPI == True
    ```

  - 反之，请修改：

  - ```python
    overrideHDPI == False
    ```

- 

