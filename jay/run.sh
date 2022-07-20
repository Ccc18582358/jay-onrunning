#!/bin/sh

x=0
while [[ $x -eq 0 || ${repeated} -eq 1 ]]
 do

   scrapy crawl ${spider}\
    -a crawlid=${crawlid}\
    -a callback=${callback}\
    -a type=${type}\
    -a priority=${priority}\
    -a full=${full}\
    -a extended=${extended}\
    -a force=${force}\
    -a meta=${meta}\
    -a urls=${urls}
  if [ $? -ne 0 ];then
    break
  fi
  if [ ${repeated} -eq 1 ];then
    sleep $((${delay}*60))
  fi
  ((x++))
  done