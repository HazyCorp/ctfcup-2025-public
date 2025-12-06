#!/bin/bash

N=10
OUTPUT_DIR="output-checker"
ADDR=172.16.206.131:31443

# Очищаем директорию от предыдущих запусков
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

GLOBAL_START=$(date +%s.%N)
START_TIMES=()
for i in $(seq 1 $N); do
  START_TIMES+=($(date +%s))
  python3 checker/checker.py test $ADDR > "$OUTPUT_DIR/process_$i.log" 2>&1 &
  PID=$!
  PIDS+=("$PID")
done

echo "Processes have been started"

exit_codes=()
failed_logs=()
process_num=1
for pid in "${PIDS[@]}"; do
  wait "$pid"
  exit_code=$?
  exit_codes+=("$exit_code")

  # Вычисляем время работы
  end_time=$(date +%s)
  start_time=${START_TIMES[$((process_num-1))]}
  duration=$((end_time - start_time))

  # Извлекаем массив кодов возврата из лога
  log_file="$OUTPUT_DIR/process_${process_num}.log"
  if [ -f "$log_file" ]; then
    return_codes=$(grep "All return codes:" "$log_file" | sed 's/.*All return codes: \[\(.*\)\],.*/\1/')

    # Проверяем, отличаются ли коды от ожидаемых [101, 101, 101, 101, 101]
    if [ "$return_codes" != "101, 101, 101, 101, 101" ]; then
      echo "Процесс $process_num завершен за ${duration}s. Return codes: [$return_codes]"
      # Помечаем лог для сохранения
      failed_logs+=("$log_file")
    else
      echo "Процесс $process_num завершен за ${duration}s. ✓"
    fi
  else
    echo "Процесс $process_num завершен за ${duration}s с кодом: $exit_code"
  fi

  ((process_num++))
done

GLOBAL_END=$(date +%s.%N)
TOTAL_TIME=$(echo "$GLOBAL_END - $GLOBAL_START" | bc)

# Подсчет успешных процессов
SUCCESSFUL=0
for code in "${exit_codes[@]}"; do
  if [ "$code" -eq 0 ]; then
    ((SUCCESSFUL++))
  fi
done

# Подсчет общего количества HTTP запросов из логов (urllib строки с "HTTP/1.1")
TOTAL_REQUESTS=0
for i in $(seq 1 $N); do
  log_file="$OUTPUT_DIR/process_$i.log"
  if [ -f "$log_file" ]; then
    req_count=$(grep -c 'HTTP/1.1' "$log_file" 2>/dev/null || echo "0")
    TOTAL_REQUESTS=$((TOTAL_REQUESTS + req_count))
  fi
done

# Вычисляем RPS
if [ $(echo "$TOTAL_TIME > 0" | bc) -eq 1 ]; then
  RPS=$(echo "scale=2; $TOTAL_REQUESTS / $TOTAL_TIME" | bc)
else
  RPS="N/A"
fi

# Переименовываем failed логи и удаляем успешные
for i in $(seq 1 $N); do
  log_file="$OUTPUT_DIR/process_$i.log"
  if [ -f "$log_file" ]; then
    # Проверяем, есть ли этот файл в списке failed
    is_failed=false
    for failed_log in "${failed_logs[@]}"; do
      if [ "$failed_log" = "$log_file" ]; then
        is_failed=true
        break
      fi
    done

    if [ "$is_failed" = true ]; then
      # Переименовываем failed лог
      mv "$log_file" "$OUTPUT_DIR/process_${i}_FAILED.log"
    else
      # Удаляем успешный лог
      rm "$log_file"
    fi
  fi
done

echo ""
echo "========================================"
echo "Статистика выполнения:"
echo "Общее время: ${TOTAL_TIME}s"
echo "Успешных процессов: $SUCCESSFUL/$N"
echo "Failed процессов: ${#failed_logs[@]}"
echo "Всего HTTP запросов: $TOTAL_REQUESTS"
echo "RPS: $RPS req/s"
echo "========================================"

if [ ${#failed_logs[@]} -gt 0 ]; then
  echo ""
  echo "Failed логи сохранены в $OUTPUT_DIR/*_FAILED.log"
fi

