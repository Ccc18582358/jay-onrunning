#!/bin/sh
# 基础依赖 打包并上传到192.168.200.51/spiders
docker buildx build --platform linux/amd64 --ssh default -t jay-requirements -f Dockerfile-requirements --build-arg HTTPS_PROXY="http://192.168.202.202:1087" .
docker tag jay-requirements 192.168.200.51/spiders/jay-requirements
docker push 192.168.200.51/spiders/jay-requirements

