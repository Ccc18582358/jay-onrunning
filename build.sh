#!/bin/sh
#SPIDER_PATH=`pwd`
#array=(`echo $SPIDER_PATH | tr '-' ' '` )
#SPIDER="${array[-1]}"
SPIDER="onrunning"
ssh-add
DOCKER_BUILDKIT=1 docker build --ssh default --no-cache -t ${SPIDER} -f Dockerfile . --build-arg spider=$SPIDER
docker tag ${SPIDER} 192.168.200.51/spiders/jay-${SPIDER}
docker push 192.168.200.51/spiders/jay-${SPIDER}