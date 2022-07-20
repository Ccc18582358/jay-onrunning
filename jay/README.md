# jay

## rocketmq 安装方法

1.安装librocketmq

mac:
```
wget https://github.com/apache/rocketmq-client-cpp/releases/download/2.0.0/rocketmq-client-cpp-2.0.0-bin-release.darwin.tar.gz
tar -xzf rocketmq-client-cpp-2.0.0-bin-release.darwin.tar.gz
cd rocketmq-client-cpp
mkdir /usr/local/include/rocketmq
cp include/* /usr/local/include/rocketmq
cp lib/* /usr/local/lib
install_name_tool -id "@rpath/librocketmq.dylib" /usr/local/lib/librocketmq.dylib
```

debian:
```
wget https://github.com/apache/rocketmq-client-cpp/releases/download/2.0.0/rocketmq-client-cpp-2.0.0.amd64.deb
sudo dpkg -i rocketmq-client-cpp-2.0.0.amd64.deb
```

centos:
```
wget https://github.com/apache/rocketmq-client-cpp/releases/download/2.0.0/rocketmq-client-cpp-2.0.0-centos7.x86_64.rpm
sudo rpm -ivh rocketmq-client-cpp-2.0.0-centos7.x86_64.rpm
```

2.安装rocketmq-client-python

```
pip install rocketmq-client-python
```