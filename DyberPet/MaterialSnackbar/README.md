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

- 

