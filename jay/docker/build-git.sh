#! /bin/bash

function git_check_uncommited(){
if output=$(git status --porcelain) && [ -z "$output" ]; then
  # git status --short
    echo "clean"
else
    echo "not clean:"
    echo "$output"
    exit 1
fi
}

ssh-add ~/.ssh/id_rsa
# 首先检查jay代码
cd ..
git_check_uncommited
# 再检查具体的spider
cd ..
git_check_uncommited
SPIDER=$(sed '/^project = /!d;s/.*= //' scrapy.cfg)

DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 --build-arg spider="${SPIDER}" --ssh default --no-cache -t "jay-${SPIDER}" -f jay/docker/Dockerfile-git .
docker tag jay-"$SPIDER" 192.168.200.51/spiders/jay-"$SPIDER"
docker push 192.168.200.51/spiders/jay-"$SPIDER"

