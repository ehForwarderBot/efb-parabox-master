########################################################################
EFB Parabox Master Channel：EFB Parabox 主端（EPM）
########################################################################
.. image:: https://img.shields.io/pypi/v/efb-parabox-master.svg
   :target: https://pypi.org/project/efb-parabox-master/
   :alt: PyPI release

.. image:: https://pepy.tech/badge/efb-parabox-master/month
   :target: https://pepy.tech/project/efb-parabox-master
   :alt: Downloads per month

**信道 ID**: ``ojhdt.parabox``

EPM 是一个用于 EH Forwarder Bot 的 Parabox 主端。需结合 Parabox WS 扩展 `parabox-extension-ws`_\ 使用。

.. _parabox-extension-ws: https://github.com/Parabox-App/parabox-extension-ws

本项目的大量代码修改自 `efb-telegram-master`_\  。

.. _efb-telegram-master: https://github.com/ehForwarderBot/efb-telegram-master

依赖
====

* Python >= 3.6

* EH Forwarder Bot >= 2.1.1.dev1

使用步骤
========

1. 安装所需的依赖

2. 安装 EPM

    ::
       pip3 install -U git+https://github.com/ojhdt/efb-parabox-master.git

    或

    ::
       pip3 install efb-parabox-master

3. 使用 *EFB 配置向导* 启用和配置 EPM，或在配置档案的 ``config.yaml`` 中手动启用。

    根据您的个人配置档案，目录路径可能有所不同。

    ::
       efb-wizard

4. 配置主端（手动配置说明如下）

手动配置
========
    配置文件存储在 ``<配置档案目录>/ojhdt.parabox/config.yaml`` 上。
    ::
        # ======================================
        # EFB Parabox Master Configuration file
        # ======================================
        #
        # This file configures how EFB Parabox Master Channel (EPM) works, and
        # Who it belongs to.
        #
        # Required items
        # --------------
        #
        # [Server Host]
        # By default the 127.0.0.1 is used which allows connections only from the current machine. If you wish to allow all network machines to connect, you need to pass 0.0.0.0 as hostname.
        host: 0.0.0.0

        # [Server Port]
        # The port clients will need to connect to.

        port: 8000

        # [Connection Token]
        # The token used for verification.

        token: abcdefghij

已知问题
======
以下问题为在测试中发现，并可能于后续版本修复的问题：

* 高频率发送 ``图片`` 将导致部分图片丢失。

* 发送过大的 ``图片`` / ``文件`` 时可能会失败。

* 偶发性的无故断连，可尝试使用 ws 扩展的 ``自动重连`` 功能临时解决。

