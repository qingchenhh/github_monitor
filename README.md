# GitHub工具监测小脚本

其实网上有好些脚本了，比如yhy0大佬的：https://github.com/yhy0/github-cve-monitor

我是参考了他的工具，因为我原先也不知道GitHub更新机制可以从GitHub的api中获取到信息，然后判断。

---

为啥有这个工具？就是当时使用yhy0大佬的工具的时候我只是单纯的想监控工具，不想监控什么关键字呀什么用户呀之类的。然后还发先跑起来的时候有两个工具一直在重复推送消息给我（后来发现是同名工具导致的），然后就想自己写一个，毕竟大佬的代码太复杂了不想看呀，其次也想自己尝试一下写写。

我这个工具就比较low了，只能做到工具监测，而且只能server酱和企业微信机器人推送。

# 工具的使用

需要装一下requests库，使用了清华大学的镜像，快一些，命令如下：

```
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
```

然后把工具一行一个的写道tools.txt中。

配置一下GitHub的token和server酱的SendKey就好了或者企业微信机器人的key。

github的token怎么获取可以百度。

![1679386101670](images/1679386101670.png)

最后使用放到服务器上，用nohup在后台跑着就行了，命令如下：

```
nohup python3 github_monitor.py &
```

# 测试结果

![1679386529979](images/1679386529979.png)

