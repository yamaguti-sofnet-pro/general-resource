#!/bin/bash
descriptions_and_commands=(
  # "説明" と "コマンド" を交互に並べる
  # "説明" は文字列の先頭を「1から初まる数値をインクリメント」として並べる
  # "コマンド" は余分なホワイトスペースを含めてはならない
  "1. 現在フォルダとファイル一覧を表示する"
  "pwd;ls -alF"
  "2. build_secureとsecure-reportフォルダを削除→build_secureフォルダ作成→移動→cmake"
  "rm -r build_secure secure-report;mkdir build_secure;cd build_secure;date"
  "3. localCoverityスクリプト内容を確認する"
  "less /mnt/c/Users/geosword/work/coveru.sh"
  "4. localCoverityを実行する"
  "cat coveru.sh"
  "5. 親フォルダに移動する"
  "cd .."
  "6. ../secure-report/output/secureフォルダを.tar.xzに圧縮する"
  "tar -Jcf ./coveru.tar.xz -C ./secure-report/output secure"
)

function AnalyzeDescriptionsAndCommands() 
{
  local -i input_line_index=0
  for line1 in "${descriptions_and_commands[@]}"; do
    local -i index=input_line_index/2
    if [[ ++input_line_index-1 -eq index*2 ]]; then
      descriptions[index]=${line1}
    else
      commands[index]=${line1}
    fi
  done
}

function ClearScreen () {
  # スクロールバーがちっちゃくなりにくにようにしたい為 Clear は使わない
  exec < /dev/tty
  local OLD_STTY=$(stty -g)
  stty raw -echo min 0
  echo -ne "\e[6n" > /dev/tty
  IFS=';' read -r -d R -a cursor_position
  stty ${OLD_STTY}
  # parse row and column
  local cursor_row=${cursor_position[0]:2}	
  local row
  for row in $(seq 1 ${cursor_row}); do
    echo -n $'\e[1A'$'\e[2K'
  done
}

function DisplayPrompt()
{
  if [[ $1 -eq 999 ]]; then
    ClearScreen
  fi
  echo "========================================================"
  echo "> 処理を選択してください :"
  for ((index=0; index<${#commands[@]}; ++index)); do
    echo "  ${descriptions[index]}"
  done
  echo "  999. CLS"
  echo "  0. 終了"
}

function EditCommand()
{
  local -i line=10
  local modify_text=""
  local nest1 nest2 nest3 nest4 nest5 terms
  while [[ $line -ne 0 ]]; do
    echo "    "${commands[$(($1-1))]}
    nest1=${commands[$(($1-1))]}
    IFS=';' read -ra nest2 <<< "${nest1}"
    index=9
    for nest3 in "${nest2[@]}"; do
      IFS=' ' read -ra nest4 <<< "${nest3}"
      for nest5 in "${nest4[@]}"; do
        terms[$((++index))]=${nest5}
        echo $index : ${nest5}
      done
    done
    echo " 0 : <編集終了>"
    echo -n "   ? "
    line=0
    read line
    if [[ $line -ge 10 ]] && [[ $line -le $index ]]; then
      echo "< (${line})変更前 :"
      echo ${terms[$line]}
      echo "> (${line})変更前 (入力してください) :"
      read modify_text
      # ココ真面目に作ってない
      commands[$(($1-1))]=${commands[$(($1-1))]//${terms[$line]}/${modify_text}}
    fi
  done
}

function ExecuteCommand()
{
  local commands1=${commands[$((order-1))]}
  local commands2
  IFS=';' read -ra commands2 <<< "${commands1}"
  echo "--------------------------------------------------------"
  for command3 in "${commands2[@]}"; do
    echo "........................................................"
    echo "> > > $command3"
    eval ${command3}
  done
}

function WhetherToExecute()
{
  echo "> > 次のコマンドを [D]編集しますか？ [X]実行しますか？ [Q]中断しますか？(d/x/Q) :"
  echo "    ${commands[$1]}"
  echo -n "    ? "
  local yes_or_no
  read yes_or_no
  case ${yes_or_no} in
    [dD]*)
      EditCommand ${order};;
    [xX]*)
      ExecuteCommand ${order};;
    *)
      echo "    中断します"
      sleep 1.5;;
  esac
}

# main()
# {
AnalyzeDescriptionsAndCommands
declare -i order=999;
while [[ order -ne 0 ]]; do
  DisplayPrompt $order
  read -p "  ? " order
  if [[ order -ne 0 ]]; then
    WhetherToExecute $((order-1))
  fi
done
# }
