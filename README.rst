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

EPM 是一个用于 EH Forwarder Bot 的 Parabox 主端。需结合 Parabox WS 扩展 `parabox-extension-ws`_\  使用。

.. _parabox-extension-ws: https://github.com/Parabox-App/parabox-extension-ws

本项目的大量代码修改自 `efb-telegram-master`_\  。

.. _efb-telegram-master: https://github.com/ehForwarderBot/efb-telegram-master

`使用教程`_\

.. _使用教程: https://blog.ojhdt.com/20221221/efb-parabox-master/


依赖
====

* Python >= 3.6

* EH Forwarder Bot >= 2.1.1.dev1

使用步骤
========

1. 安装所需的依赖

2. 安装 EPM

   .. code:: bash

    pip3 install -U git+https://github.com/ojhdt/efb-parabox-master.git

   或

   .. code:: bash

    pip3 install efb-parabox-master

3. 使用 *EFB 配置向导* 启用和配置 EPM，或在配置档案的 ``config.yaml`` 中手动启用。

   根据您的个人配置档案，目录路径可能有所不同。

   .. code:: bash

    efb-wizard

4. 配置主端（手动配置说明如下）

手动配置
========
配置文件存储在 ``<配置档案目录>/ojhdt.parabox/config.yaml`` 上。

.. code:: yaml

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

    # [Message Sending Interval]
    # The time interval for getting messages to send from the database. If the time is too short,
    # it will cause high-frequency query of the database, if the time is too long, it will cause a
    # long receiving delay. The unit is second.

    sending_interval: 3

    # [Compatibility Mode]
    # Compatibility mode is used to enable compatibility with slaves that does not support the
    # feature of obtaining group members' avatars.
    # It SHOULD NOT be enabled most of the time.

    compatibility_mode: true

    #
    # Experimental Options
    # --------------
    #
    enable_fcm: false

    fcm_token: device_fcm_token

    object_storage:
      #  type: tencent_cos
      #  secret_id: your_permanent_secret_id
      #  secret_key: your_permanent_secret_key
      #  bucket: examplebucket-1250000000
      #  region: ap-guangzhou
      #
      #  type: qiniu
      #  access_key: your_permanent_access_key
      #  secret_key: your_permanent_secret_key
      #  bucket: your_bucket_name
      #  domain: your_bucket_domain
      #


有关 FCM 模式（实验性）的说明
=========
该模式为实验性工作模式，默认禁用。需手动修改配置文件（ ``enable_fcm`` ）启用。启用后，常规模式下的配置项将失效（主机，端口，密钥等）。你还需提供从 Parabox 中获取的 FCM token。建议同步运行 Parabox 中 ``配置FCM连接`` 向导，该向导将指引你完成有关配置步骤。

由于 FCM 仅允许传输文本，图片/语音/文件等消息类型无法正常传输，需自行配置对象存储。目前仅支持腾讯云/七牛云。若需启用，请删除 ``object_storage`` 配置项下对应对象存储服务的 ``#`` 注释，并按提示填充配置项。请注意，Parabox 中配置的对象存储服务需与本主端保持一致。

FCM 传输限额为 **4000** 条/小时/设备。

受 FCM 机制限制，所有消息皆须经过 Parabox 公共消息中转服务器（ ``api.parabox.ojhdt.dev`` ）中转。该过程不会记录您的任何聊天数据。

若本主端与中转服务器断开后重连，目前已建立对话的发送信道都将失效（将无法正常发送消息）。仅需使对话再接收至少一条消息即可刷新发送信道。


已知问题
=========

以下问题为在测试中发现，并可能于后续版本修复的问题：

* 发送过大的 ``图片`` / ``文件`` 时可能会失败。

