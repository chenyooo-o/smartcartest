#M0-1

##选择虚拟机VirtualBox
-起初是打算使用wsl2的，安装为wsl2的过程中发现：1. 很多教程的方法都不一样，而且某些教程由于版本过低等原因不可用； 2.了解了虚拟机之后，觉得虚拟机的 图形化界面很方便，容易理解，感觉比较适合我，于是改用虚拟机
-参照鱼香ROS的教程下载并设置了虚拟机https://www.bilibili.com/video/BV14M4m117LJ?spm_id_from=333.788.videopod.sections&vd_source=cdbcfc731bb13e23911a08fe68c619b4

##环境搭建
| 组件 | 查阅资料 | 出现的问题 | 报错原文 | 解决方法 | 备注 |
|------|------|------|------|------|
|ubuntu|https://www.bilibili.com/video/BV14M4m117LJ?spm_id_from=333.788.videopod.sections&vd_source=cdbcfc731bb13e23911a08fe68c619b4|本机清华镜像源不可用|-|改用中科大源|-|
|ROS2|https://www.bilibili.com/video/BV1Jz421B7Ey?spm_id_from=333.788.videopod.sections&vd_source=cdbcfc731bb13e23911a08fe68c619b4|本机清华镜像源不可用|-|改用中科大源|-|
|python虚拟环境| https://github.com/astral-sh/uv|起初打算安装conda，但发现清华、北外镜像源不可用，中科大源协议不正确，上交等镜像源找不到conda相应安装链接；anaconda官网太慢|yyo@yyo-VirtualBox:-/downloads$ wget ^[[200~https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-py39_24.7.1-0-Linux-x86_64. sh~
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-py39_24.7.1-0-Linux-x86_64.sh-：地址缺少协议类型. |改安装uv|-|
|C/C++|-|-|-|-|查看编译器版本后发现可用|
|编辑器|-|-|-|-|在vscode扩展中安装|
|版本控制git|https://www.bilibili.com/video/BV1B14y1J79b/?spm_id_from=333.337.search-card.all.click|github不再支持用账号密码直接push代码|remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: 鉴权失败|虚拟机终端生存ssh密钥对，在github添加公钥，把仓库从https地址切换成ssh地址|-|

##远程登录（windows连接到虚拟机）
-一开始显示connect timed out，连不上虚拟机
-virtualbox默认NAT模式，需要做端口转发
-将虚拟机网络的连接方式改为桥接网卡，再次获取虚拟机ip，此时windows可以连接上虚拟机
