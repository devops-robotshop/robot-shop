import requests
import pandas as pd
import time
from datetime import datetime

PROMETHEUS_URL = 'http://localhost:9090/api/v1/query'

QUERIES = {
    'cpu_usage': 'sum(rate(container_cpu_usage_seconds_total{namespace="production", container!=""}[1m]))',
    'network_rx_rps': 'sum(rate(container_network_receive_packets_total{namespace="production"}[1m]))',
    'memory_usage_mb': 'sum(container_memory_working_set_bytes{namespace="production", container!=""}) / 1024 / 1024',
    'restart_rate': 'sum(rate(kube_pod_container_status_restarts_total{namespace="production"}[1m]))'
}

def get_metric(query):
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': query})
        data = response.json().get('data', {}).get('result', [])
        if data:
            return round(float(data[0]['value'][1]), 4)
        return 0.0
    except:
        return 0.0

def collect_data(label, duration_minutes=15):
    end_time = time.time() + (duration_minutes * 60)
    data_rows = []

    while time.time() < end_time:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cpu = get_metric(QUERIES['cpu_usage'])
        rx_rps = get_metric(QUERIES['network_rx_rps'])
        mem_mb = get_metric(QUERIES['memory_usage_mb'])
        restarts = get_metric(QUERIES['restart_rate'])

        row = {
            'timestamp': timestamp,
            'cpu_usage': cpu,
            'network_rx_rps': rx_rps,
            'memory_usage_mb': mem_mb,
            'restart_rate': restarts,
            'label': label
        }
        data_rows.append(row)
        
        print(f"[{timestamp}] CPU: {cpu:.4f} | Net_RX(proxy RPS): {rx_rps:.1f} | Mem(MB): {mem_mb:.1f} | Restarts(proxy Error): {restarts:.4f} | Label: {label}")
        
        time.sleep(15)

    filename = f"dataset_label_{label}_{int(time.time())}.csv"
    df = pd.DataFrame(data_rows)
    df.to_csv(filename, index=False)
    print(f"DONE: {filename}")

if __name__ == "__main__":
    CURRENT_LABEL = 2
    collect_data(label=CURRENT_LABEL, duration_minutes=15)