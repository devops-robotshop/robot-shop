import time
import requests
import pandas as pd
import joblib
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from datetime import datetime

# ==================================================
# 1. CẤU HÌNH KẾT NỐI
# ==================================================
PROMETHEUS_URL = "http://localhost:9090"
PUSHGATEWAY_URL = "localhost:9091"
MODEL_PATH = "rf_model_20260525_162936.pkl"  # Đảm bảo tên file khớp 100%

# Load mô hình AI
print("[Khởi động] Đang tải não bộ AI...")
model = joblib.load(MODEL_PATH)
print("[OK] Đã kết nối với Model RF.")

# ==================================================
# 2. CẤU HÌNH ĐẨY DATA (PUSHGATEWAY)
# ==================================================
registry = CollectorRegistry()

# Biến 1: Dành cho KEDA (Chỉ dùng khi cần đẻ Pod Web chống bão)
ai_metric = Gauge('ai_predicted_anomaly', 'AI prediction for KEDA (0=Normal, 10=Scale)', registry=registry)

# Biến 2: Dành cho AlertManager (Chỉ dùng khi cần báo động hệ thống sập qua Telegram/Mail)
ai_infra_error = Gauge('ai_infra_error', 'AI prediction for AlertManager (0=Normal, 1=Error)', registry=registry)

# ==================================================
# 3. HÀM QUÉT DỮ LIỆU LIVE TỪ PROMETHEUS
# ==================================================
def fetch_live_metrics():
    queries = {
        "cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{namespace="production",container!="",container!="POD"}[1m])) or vector(0)',
        "network_rx_rps": 'sum(rate(container_network_receive_packets_total{namespace="production"}[1m])) or vector(0)',
        "memory_usage_mb": '(sum(container_memory_working_set_bytes{namespace="production",container!="",container!="POD"}) / 1048576) or vector(0)',
        "payment_cpu": 'sum(rate(container_cpu_usage_seconds_total{namespace="production",pod=~"payment.*",container!=""}[1m])) or vector(0)',
        "restart_rate": 'sum(rate(kube_pod_container_status_restarts_total{namespace="production"}[1m])) or vector(0)',
        "pod_restarts_5m": 'sum(increase(kube_pod_container_status_restarts_total{namespace="production"}[5m])) or vector(0)'
    }
    
    live_data = {
        'cpu_usage': 0.0, 'cpu_delta': 0.0, 'network_rx_rps': 0.0, 'net_delta': 0.0,
        'memory_usage_mb': 0.0, 'http_error_rate': 0.0, 'p99_latency_ms': 0.0,
        'rabbitmq_queue': 0.0, 'payment_cpu': 0.0, 'restart_rate': 0.0, 'pod_restarts_5m': 0.0
    }

    try:
        for name, query in queries.items():
            response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': query})
            results = response.json().get('data', {}).get('result', [])
            if results:
                live_data[name] = float(results[0]['value'][1])
        return live_data
    except Exception as e:
        print(f"[Lỗi] Không thể lấy data từ Prometheus: {e}")
        return None

# ==================================================
# 4. VÒNG LẶP DỰ ĐOÁN (THE HEARTBEAT)
# ==================================================
print("\n" + "="*50)
print("HỆ THỐNG AIOps - PREEMPTIVE SCALING & ALERTING KÍCH HOẠT")
print("="*50)

while True:
    now = datetime.now().strftime("%H:%M:%S")
    
    data = fetch_live_metrics()
    if data is None:
        time.sleep(5)
        continue
        
    df = pd.DataFrame([data])
    
    # Ép kiểu dữ liệu để tránh Warning của Model (Đồng bộ thứ tự cột)
    df = df[['cpu_usage', 'cpu_delta', 'network_rx_rps', 'net_delta', 'memory_usage_mb', 'payment_cpu', 'restart_rate', 'pod_restarts_5m']]
    # Thứ tự chèn đúng khớp 11 features của model
    df.insert(5, 'http_error_rate', 0.0)
    df.insert(6, 'p99_latency_ms', 0.0)
    df.insert(7, 'rabbitmq_queue', 0.0)

    prediction = model.predict(df)[0]
    
    # ==================================================
    # LOGIC CỐT LÕI 
    # ==================================================
    if prediction == 1 and data['network_rx_rps'] >= 100:
        # TRƯỜNG HỢP 1: BÃO TRAFFIC (Spike thực sự)
        status_text = "🔴 BÃO TRAFFIC -> KÍCH HOẠT KEDA!"
        ai_metric.set(10)      # Bắn hệ số 10 để ép KEDA đẻ max Pod
        ai_infra_error.set(0)  # Hệ thống không lỗi, không cần báo Telegram
        
    elif prediction == 2:
        # TRƯỜNG HỢP 2: LỖI HẠ TẦNG (Error - VD: Payment sập)
        # Bỏ qua chỉ số RPS (vì lỗi thì RPS có thể giảm sâu)
        status_text = "🟠 LỖI HỆ THỐNG -> KÍCH HOẠT ALERTMANAGER!"
        ai_metric.set(0)       # Web không bị tải cao, không cần scale Web
        ai_infra_error.set(1)  # Bắn cờ 1 để AlertManager gửi Telegram
        
    else:
        # TRƯỜNG HỢP 3: BÌNH THƯỜNG (Hoặc nhiễu RPS dỏm dưới 100)
        status_text = "🟢 BÌNH THƯỜNG"
        ai_metric.set(0)       # KEDA off
        ai_infra_error.set(0)  # AlertManager off

    try:
        push_to_gateway(PUSHGATEWAY_URL, job='ai_ops', registry=registry)
        print(f"[{now}] Net RPS: {data['network_rx_rps']:>4.0f} | Quyết định AI: {status_text}")
    except Exception as e:
        print(f"[{now}] Lỗi gửi cảnh báo lên Pushgateway: {e}")
        
    time.sleep(10)