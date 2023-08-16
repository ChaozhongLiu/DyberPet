# DyberPet存档系统 · 改

## 简介

本次更新对<code>v0.2.2</code>实装的更新系统进行了改善，修复了已知bug并且新增了一些功能。



## 设置

如果计算机上的DyberPet工程使用的是旧版的存档系统，请先删除旧版package并参考安装存档系统时参考的<a href='https://github.com/ChaozhongLiu/DyberPet/pull/5'>文档</a>撤销对<code>DyberPet.py</code>的修改。



如果DyberPet自身没有开启HDPI缩放（<code>QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)</code>），则需要通过<code>overrideHDPI</code>参数来开启窗体的HDPI支持，需要在<code>StartBackupManager.py</code>中修改：

```python
overrideHDPI = True    # 请在主程序未开启HDPI缩放的情况下开启以在本窗口上支持HDPI缩放
```



*<del>您也可以选择在此情况下不开启HDPI支持，但是在系统缩放 > 100%的显示器上可能会显得程序字体和图标偏小。</del>*



## 更新日志

- **v.0.2.2.1-b**: 