#!/bin/bash
# 用法: ./review_pr.sh [文件路径]
# 不带参数则显示交互式菜单，选择文件打开对比

REPO=/data/haotianwu/biojson
BASE=main
PR=pr-review

open_diff() {
  FILE=$1
  NAME=$(echo "$FILE" | tr '/' '_')
  cd "$REPO"
  git show $BASE:"$FILE" > /tmp/${NAME}_main.py 2>/dev/null || echo "# 文件在 main 中不存在（新增文件）" > /tmp/${NAME}_main.py
  git show $PR:"$FILE" > /tmp/${NAME}_pr.py 2>/dev/null || echo "# 文件在 PR 中不存在（已删除文件）" > /tmp/${NAME}_pr.py
  echo "打开对比: $FILE"
  code --diff /tmp/${NAME}_main.py /tmp/${NAME}_pr.py
}

if [ -n "$1" ]; then
  open_diff "$1"
else
  cd "$REPO"
  # 获取改动文件列表
  mapfile -t FILES < <(git diff $BASE...$PR --name-only)

  echo ""
  echo "PR #1 改动的文件列表："
  echo "================================"
  for i in "${!FILES[@]}"; do
    printf " %2d) %s\n" "$((i+1))" "${FILES[$i]}"
  done
  echo ""
  echo " 0) 退出"
  echo ""

  while true; do
    read -rp "请输入编号打开对比（0 退出）: " choice
    if [[ "$choice" == "0" ]] || [[ -z "$choice" ]]; then
      echo "退出"
      break
    elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#FILES[@]}" ]; then
      open_diff "${FILES[$((choice-1))]}"
    else
      echo "无效编号，请重新输入"
    fi
  done
fi
