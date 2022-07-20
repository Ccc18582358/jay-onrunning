cd ../..
SPIDER=$(sed '/^project = /!d;s/.*= //' scrapy.cfg)

DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 --build-arg spider="${SPIDER}" --ssh default --no-cache -t "jay-${SPIDER}" -f jay/docker/Dockerfile-local .
docker tag jay-"$SPIDER" 192.168.200.51/spiders/jay-"$SPIDER"
docker push 192.168.200.51/spiders/jay-"$SPIDER"


