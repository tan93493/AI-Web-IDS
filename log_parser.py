import pandas as pd

LOG_FILE = 'logs/access.log'

def parse_log(file_path):
    data = []
    skipped_lines = 0
    with open(file_path, 'r') as f:
        for line_number, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) < 5:
                print(f"Skipping line {line_number}: not enough parts -> {parts}")
                skipped_lines += 1
                continue
            
            timestamp = f"{parts[0]} {parts[1]}"
            ip = parts[2]
            method = parts[3]
            path = parts[4]
            data.append({'timestamp': timestamp, 'ip': ip, 'method': method, 'path': path})
    
    df = pd.DataFrame(data)
    print(df)
    if skipped_lines > 0:
        print(f"Skipped {skipped_lines} invalid lines.")

if __name__ == '__main__':
    parse_log(LOG_FILE)
