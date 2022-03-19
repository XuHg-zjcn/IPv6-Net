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
1. 运行daemon.py文件
2. 手动修改data.db
3. 添加开机启动
   ```bash
   sudo cp files/ipv6netd /etc/init.d  #复制启动脚本
   sudo update-rc.d ipv6netd defaults  #更新自动启动
   ```
   下次开机就能自动启动了

# 更新计划
1. 命令行修改数据库
2. 实现数据库同步
3. 数字签名，优先选用Ed25519
4. 加密通信

# 版本历史
## v0.1.0: (2022.3.19)
  实现了一些简单功能，自动同步IPv6地址，记录一些信息
  添加了README文档