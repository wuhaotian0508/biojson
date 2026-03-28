#!/usr/bin
name=$1
channel=$2
echo "你好, $name! 你加入了 $channel 频道!"

while true
do
number=$(shuf -i 1-10 -n 1)
echo $number
echo "请输入一个1-10之间的数字:"
read guess
if [[ $guess -eq $number ]]; then
  echo "恭喜你，猜对了！是否继续游戏？(y/n)"
    read answer
    if [[ $answer -eq 'y' ]]||[[ $answer -eq 'Y' ]]; then
        continue
    else
        echo "游戏结束，感谢参与！"
        break
    fi
elif [[ $guess -gt $number ]]; then
  echo "你猜的数字太大了！"
else
  echo "你猜的数字太小了！"
fi
done