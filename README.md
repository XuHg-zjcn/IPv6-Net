# IPv6 Net
一个分布式IPv6地址同步网络

# 背景介绍
目前我的宽带和手机流量能获取动态公网IPv6地址，每次IPv6地址变化后都需要手动修改，很麻烦。  
我不想使用第三方的DDNS解析服务，自己实现一个IPv6地址同步工具。  

# 协议介绍
每个设备储存一份数据库，含有其他设备的名称，局域网IPv4，公网IPv6地址等信息。  
当设备间能通信时（都处于局域网中，知道对方IPv6等）时，实时同步数据库，并写入hosts文件中。  
具体协议请看[docs/spec.md](docs/spec.md)  

# 安装方法
1. 安装依赖库`sudo pip3 install prettytable ed25519`(如果需要写入hosts，必须root用户安装)
1. 添加开机启动  
   把*files/ipv6netd*文件中的`WORKDIR`改为您的安装目录
   ```bash
   sudo cp files/ipv6netd /etc/init.d  #复制启动脚本
   sudo update-rc.d ipv6netd defaults  #更新自动启动
   ```
   下次开机就能在后台自动启动了

写入系统hosts需要root权限，如果不需要写入，可以将*conf.py*中`hosts_file`设置为其他路径。  

# 使用方法
1. 在至少两台机器上安装该软件
1. 配置时需要停止*daemon.py*，如果在后台运行请用`sudo service ipv6netd stop`停止
1. `./cli.py`->`2`查看底部公钥(第一次运行会自动生成)
1. `./cli.py`->`1`添加节点，按照提示填写信息
1. 双方都添加对方节点才能顺利连接
1. (可选)在hosts文件的`# IPv6Net Start`和`# IPv6Net End`之间插入想要写入hosts的节点  
   IPv6地址不足39个字符必须用空格补上，中间用`\t`制表符分割，主机名为节点名+*conf.py*中的`domain_suffix`
1. 在A机和B机上同时运行*daemon.py*  
   可以用`./daemon.py`前台运行或`sudo service ipv6netd start`后台运行

# 更新计划
1. `ip monitor address`代替定期执行`ip address ...`
1. 实现数据库同步
1. 加密通信
1. 日志记录可读指令而不是十六进制
1. 使用try防止出错
1. 添加更多配置选项
1. 全部数据都进行签名
1. 更新通信协议，使用key,value模型，可自定义扩展
1. 同时发布多个地址, 按照网关MAC地址来判断是否为同一个
1. 制作Windows, Android, MCU版本
1. 英文文档和操作界面

# 版本历史
## v0.1.0: (2022.3.19)
- 实现了一些简单功能，自动同步IPv6地址，记录一些信息
- 添加了README文档

## v0.2.0: (2022.5.14)
- CLI操作界面
- ed25519签名
- 更新通信协议
