#!/bin/bash
# 内存使用情况分析脚本

echo "========================================="
echo "系统内存使用情况分析"
echo "========================================="
echo ""

echo "【1. 总体内存情况】"
echo "-----------------------------------------"
free -h
echo ""

echo "【2. Swap 使用情况】"
echo "-----------------------------------------"
swapon --show
if [ $? -ne 0 ]; then
    echo "未启用 swap 空间"
fi
echo ""

echo "【3. 内存占用 TOP 10 进程】"
echo "-----------------------------------------"
printf "%-8s %-8s %-10s %-10s %s\n" "PID" "USER" "MEM%" "MEM(MB)" "COMMAND"
echo "-----------------------------------------"
ps aux --sort=-%mem | head -11 | tail -10 | awk '{printf "%-8s %-8s %-10s %-10.1f %s\n", $2, $1, $4"%", $6/1024, $11}'
echo ""

echo "【4. 按用户统计内存使用】"
echo "-----------------------------------------"
printf "%-15s %-15s\n" "USER" "MEMORY(MB)"
echo "-----------------------------------------"
ps aux | awk '{mem[$1]+=$6} END {for (user in mem) printf "%-15s %-15.1f\n", user, mem[user]/1024}' | sort -k2 -rn | head -10
echo ""

echo "【5. Python 进程内存占用】"
echo "-----------------------------------------"
printf "%-8s %-10s %-50s\n" "PID" "MEM(MB)" "COMMAND"
echo "-----------------------------------------"
ps aux | grep python | grep -v grep | awk '{printf "%-8s %-10.1f %-50s\n", $2, $6/1024, substr($0, index($0,$11))}'
echo ""

echo "【6. Node.js 进程内存占用】"
echo "-----------------------------------------"
printf "%-8s %-10s %-50s\n" "PID" "MEM(MB)" "COMMAND"
echo "-----------------------------------------"
ps aux | grep node | grep -v grep | awk '{printf "%-8s %-10.1f %-50s\n", $2, $6/1024, substr($0, index($0,$11))}'
echo ""

echo "【7. 内存使用统计】"
echo "-----------------------------------------"
total=$(free -m | awk 'NR==2{print $2}')
used=$(free -m | awk 'NR==2{print $3}')
free=$(free -m | awk 'NR==2{print $4}')
available=$(free -m | awk 'NR==2{print $7}')
percent=$(awk "BEGIN {printf \"%.1f\", ($used/$total)*100}")

echo "总内存:     ${total} MB"
echo "已使用:     ${used} MB (${percent}%)"
echo "空闲:       ${free} MB"
echo "可用:       ${available} MB"
echo ""

# 内存压力提示
if [ $percent -ge 90 ]; then
    echo "⚠️  警告: 内存使用率超过 90%，建议清理或增加 swap"
elif [ $percent -ge 80 ]; then
    echo "⚠️  注意: 内存使用率超过 80%"
else
    echo "✅ 内存使用正常"
fi
echo ""

echo "【8. 最近 OOM (Out of Memory) 记录】"
echo "-----------------------------------------"
dmesg | grep -i "killed process" | tail -5
if [ $? -ne 0 ]; then
    echo "未发现 OOM 记录"
fi
echo ""

echo "========================================="
echo "分析完成"
echo "========================================="
