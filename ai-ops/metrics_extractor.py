import requests
import pandas as pd
import time
import sys
from datetime import datetime
 
# ==========================================
# CẤU HÌNH — ĐỔI SỐ NÀY TRƯỚC KHI CHẠY
# 0 = Normal  |  1 = Spike  |  2 = Error (scale=0)
# ==========================================
CURRENT_LABEL = 0
 
PROMETHEUS_URL = "http://localhost:9090/api/v1/query"
DURATION_MINUTES = 15
INTERVAL_SECONDS = 15
 
# ==========================================
# 6 QUERIES (Đã comment out 3 metrics gây nhiễu/không có data)
# ==========================================
QUERIES = {
    "cpu_usage": (
        'sum(rate(container_cpu_usage_seconds_total'
        '{namespace="production",container!="",container!="POD"}[1m])) or vector(0)'
    ),
    "network_rx_rps": (
        'sum(rate(container_network_receive_packets_total'
        '{namespace="production"}[1m])) or vector(0)'
    ),
    "memory_usage_mb": (
        '(sum(container_memory_working_set_bytes'
        '{namespace="production",container!="",container!="POD"}) / 1048576) or vector(0)'
    ),
    "restart_rate": (
        'sum(rate(kube_pod_container_status_restarts_total'
        '{namespace="production"}[1m])) or vector(0)'
    ),
    
    # ĐÃ BỎ QUA 3 METRICS NÀY ĐỂ TRÁNH NHIỄU DATA:
    # "http_error_rate": (
    #     'sum(rate(http_requests_total'
    #     '{namespace="production",status=~"5.*"}[1m])) or vector(0)'
    # ),
    # "p99_latency_ms": (
    #     'histogram_quantile(0.99, sum by(le) ('
    #     'rate(http_request_duration_seconds_bucket'
    #     '{namespace="production"}[1m]))) * 1000 or vector(0)'
    # ),
    # "rabbitmq_queue": (
    #     'sum(rabbitmq_queue_messages{namespace="production"}) or vector(0)'
    # ),
    
    "payment_cpu": (
        'sum(rate(container_cpu_usage_seconds_total'
        '{namespace="production",pod=~"payment.*",container!=""}[1m])) or vector(0)'
    ),
    "pod_restarts_5m": (
        'sum(increase(kube_pod_container_status_restarts_total'
        '{namespace="production"}[5m])) or vector(0)'
    ),
}
 
 
# ------------------------------------------
# KIỂM TRA PROMETHEUS CÓ SỐNG KHÔNG
# ------------------------------------------
def check_prometheus():
    try:
        r = requests.get(
            PROMETHEUS_URL,
            params={"query": 'up{job="prometheus"}'},
            timeout=5,
        )
        r.raise_for_status()
        print("[OK] Prometheus đang sống tại", PROMETHEUS_URL)
        return True
    except Exception as e:
        print(f"[LỖI] Không kết nối được Prometheus: {e}")
        print("      Hãy chắc chắn đã chạy: kubectl port-forward svc/kube-prometheus-stack-prometheus -n monitoring 9090:9090")
        return False
 
 
# ------------------------------------------
# KIỂM TRA TỪNG METRIC CÓ TRẢ DỮ LIỆU KHÔNG
# ------------------------------------------
def verify_metrics():
    print("\n[Kiểm tra metrics] Đang thử từng query...\n")
    available = {}
    for name, query in QUERIES.items():
        try:
            r = requests.get(PROMETHEUS_URL, params={"query": query}, timeout=5)
            results = r.json().get("data", {}).get("result", [])
            val = float(results[0]["value"][1]) if results else 0.0
            status = "OK" if val != 0.0 else "zero (có thể metric chưa có hoặc không hoạt động)"
            print(f"  {'[OK]' if val != 0.0 else '[--]'}  {name:25s} = {val:.4f}  ({status})")
            available[name] = True
        except Exception as e:
            print(f"  [ERR] {name:25s} — {e}")
            available[name] = False
    print()
    return available
 
 
# ------------------------------------------
# LẤY GIÁ TRỊ MỘT METRIC
# ------------------------------------------
def get_metric(query: str) -> float:
    try:
        r = requests.get(PROMETHEUS_URL, params={"query": query}, timeout=5)
        results = r.json().get("data", {}).get("result", [])
        if results:
            val = float(results[0]["value"][1])
            return round(val, 6) if not (val != val) else 0.0  # NaN check
        return 0.0
    except Exception:
        return 0.0
 
 
# ------------------------------------------
# TẠO TÊN FILE UNIQUE — KHÔNG BAO GIỜ TRÙNG
# ------------------------------------------
def make_filename(label: int) -> str:
    label_names = {0: "normal", 1: "spike", 2: "error"}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = label_names.get(label, f"label{label}")
    return f"dataset_label{label}_{name}_{ts}.csv"
 
 
# ------------------------------------------
# VÒNG LẶP THU THẬP
# ------------------------------------------
def collect(label: int, duration_minutes: int = 15):
    label_names = {0: "NORMAL", 1: "SPIKE (Bão Traffic)", 2: "ERROR (Scale=0)"}
    print(f"\n{'='*55}")
    print(f"  NHÃN: {label} — {label_names.get(label, 'UNKNOWN')}")
    print(f"  Thời gian: {duration_minutes} phút  |  Interval: {INTERVAL_SECONDS}s")
    print(f"  Ước tính: ~{int(duration_minutes * 60 / INTERVAL_SECONDS)} dòng dữ liệu")
    print(f"{'='*55}\n")
 
    end_time = time.time() + duration_minutes * 60
    rows = []
    prev_cpu = None
    prev_net = None
    idx = 0
 
    while time.time() < end_time:
        remaining = int(end_time - time.time())
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = {"timestamp": ts, "label": label}
 
        for name, query in QUERIES.items():
            row[name] = get_metric(query)
 
        # DELTA FEATURES — tốc độ thay đổi (giúp AI nhận ra "gia tốc" spike)
        row["cpu_delta"] = round(row["cpu_usage"] - prev_cpu, 6) if prev_cpu is not None else 0.0
        row["net_delta"] = round(row["network_rx_rps"] - prev_net, 4) if prev_net is not None else 0.0
 
        prev_cpu = row["cpu_usage"]
        prev_net = row["network_rx_rps"]
 
        rows.append(row)
        idx += 1
 
        mins, secs = divmod(remaining, 60)
        
        # Đã cập nhật dòng print: Xóa bỏ err=... để không bị KeyError
        print(
            f"  [{idx:03d}] {ts} | "
            f"cpu={row['cpu_usage']:.4f}  "
            f"net={row['network_rx_rps']:.1f}  "
            f"pay_cpu={row['payment_cpu']:.4f}  "
            f"còn {mins:02d}:{secs:02d}"
        )
        time.sleep(INTERVAL_SECONDS)
 
    filename = make_filename(label)
    df = pd.DataFrame(rows)
 
    # Sắp xếp cột cho dễ đọc (Đã loại bỏ 3 cột comment out)
    col_order = ["timestamp", "label",
                 "cpu_usage", "cpu_delta",
                 "network_rx_rps", "net_delta",
                 "memory_usage_mb",
                 "payment_cpu",
                 "restart_rate", "pod_restarts_5m"]
                 
    df = df[[c for c in col_order if c in df.columns]]
    df.to_csv(filename, index=False)
 
    print(f"\n[DONE] Đã lưu {len(df)} dòng → {filename}")
    print(f"       Columns: {list(df.columns)}\n")
    return filename
 
 
# ------------------------------------------
# MAIN
# ------------------------------------------
if __name__ == "__main__":
    # Nếu muốn ghi đè label từ CLI: python metrics_extractor.py 1
    label = int(sys.argv[1]) if len(sys.argv) > 1 else CURRENT_LABEL
 
    if not check_prometheus():
        sys.exit(1)
 
    # Hỏi có muốn verify metrics trước không
    ans = input("\nKiểm tra từng metric trước khi chạy? (y/n, mặc định n): ").strip().lower()
    if ans == "y":
        verify_metrics()
        input("Nhấn Enter để bắt đầu thu thập...\n")
 
    collect(label=label, duration_minutes=DURATION_MINUTES)