import os
import pandas as pd
import re
from workalendar.asia import Taiwan  # 使用 workalendar 計算台灣的工作日
import csv
from datetime import timedelta

# 創建輸出資料夾名稱
output_dir = "auction_data_processed"
os.makedirs(output_dir, exist_ok=True)

# 讀取 cleaned_auction_data.csv 檔案
cleaned_auction_data_path = "cleaned_auction_data.csv"
auction_data = pd.read_csv(cleaned_auction_data_path, encoding='utf-8')

# 1. 動態擷取 DateStart 和 DateEnd 之間的欄位，並標記偏移量
columns = auction_data.columns.tolist()
start_index = columns.index("DateStart")
end_index = columns.index("DateEnd")


date_columns_raw = columns[start_index:end_index + 1]

# 修正：正確辨識偏移格式，並檢查基礎欄位是否存在
date_columns = {}
for col in date_columns_raw:
    match = re.match(r"(.+?)([+-]\d+)$", col.strip())
    
    if match:
        base_name = match.group(1).strip()
        offset = int(match.group(2))
        
        # 檢查基礎欄位是否存在於資料中
        if base_name in auction_data.columns:
            date_columns[col] = {'base': base_name, 'offset': offset}
        else:
            # 若基礎欄位不存在，視為完整欄位名稱，無偏移
            date_columns[col] = {'base': col, 'offset': 0}
    else:
        date_columns[col] = {'base': col, 'offset': 0}
print(date_columns,"<<AAAAAAAAAAAAAAA")


# 獲取所有文件列表
all_files = [f for f in os.listdir('stockdata') if f.endswith('.csv')]

# 初始化台灣工作日計算
cal = Taiwan()

# 讀取 holidays.csv，並處理格式
holidays_path = "holidays.csv"
if os.path.exists(holidays_path):
    try:
        holidays_list = []
        with open(holidays_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                date_part = row[0].strip() if len(row) > 0 else None
                if date_part:
                    holidays_list.append(date_part)

        holidays = pd.DataFrame(holidays_list, columns=["日期"])
        holidays["日期"] = holidays["日期"].str.extract(r"(\d{4}-\d{2}-\d{2})", expand=False)
        holidays["日期"] = pd.to_datetime(holidays["日期"], errors="coerce").dt.date
        holidays_set = set(holidays["日期"].dropna())

        print(f"成功讀取 holidays.csv，共 {len(holidays_set)} 個假日")
    except Exception as e:
        print(f"讀取 holidays.csv 時發生錯誤: {e}")
        holidays_set = set()
else:
    print("找不到 holidays.csv，將不考慮假日")
    holidays_set = set()


# 2. 定義函數以獲取收盤價，並根據偏移量調整
def get_closing_price(security_id, base_date, offset=0):
    """
    根據證券代號和日期獲取收盤價，並根據偏移量調整日期（非索引位置）。
    """
    for file_name in all_files:
        if file_name.startswith(f"[{security_id}]") and file_name.endswith(".csv"):
            try:
                # Update file path to use stockdata directory
                full_path = os.path.join('stockdata', file_name)
                price_data = pd.read_csv(full_path, encoding='utf-8')
                price_data['日期'] = pd.to_datetime(price_data['日期'], errors='coerce').dt.date
                price_data = price_data.sort_values(by='日期').reset_index(drop=True)

                # Convert base_date to datetime object
                base_date_dt = pd.to_datetime(base_date, errors='coerce')
                if pd.isna(base_date_dt):
                    print(f"無效日期格式: base_date={base_date}, offset={offset}")
                    return ""
                
                # Calculate the target date by adding offset days to base_date
                from datetime import timedelta
                base_date = base_date_dt.date()
                target_date = base_date + timedelta(days=offset)
                
                # CHANGED: Added holiday check in addition to weekend check
                is_weekend = target_date.weekday() >= 5
                is_holiday = target_date in holidays_set  # NEW
                is_non_trading_day = is_weekend or is_holiday  # NEW
                
                # Look for the target date in the data
                target_data = price_data[price_data['日期'] == target_date]
                
                if not target_data.empty:
                    # Target date found
                    return target_data.iloc[0]['收盤價']
                else:
                    # CHANGED: Only print if it's a regular trading day (not weekend or holiday)
                    if not is_non_trading_day:  # CHANGED from "if not is_weekend:"

                        # Check if this date should exist (is it within the file's date range?)
                        min_date = price_data['日期'].min()
                        max_date = price_data['日期'].max()
                        if min_date <= target_date <= max_date:
                            print(f"  🈳範圍內，但沒有數據: target_date={target_date} (base_date={base_date}, offset={offset}), 檔案={file_name} 注意: 此日期在檔案日期範圍內 ({min_date} 至 {max_date})，但沒有數據 (可能是非預期的休市日)")
                        else:
                            print(f"  🚀未來日期: target_date={target_date} (base_date={base_date}, offset={offset}), 檔案={file_name} 注意: 未來日期，無法獲取數據")
                    # NEW: Optional debugging for weekend/holiday identification
                    elif is_weekend:
                        # Optional: You can uncomment if you want weekend prints
                        print(f"  🛌週末非交易日: target_date={target_date} (base_date={base_date}, offset={offset})")
                        pass
                    elif is_holiday:
                        # Optional: You can uncomment if you want holiday prints
                        print(f"  🧨假日非交易日: target_date={target_date} (base_date={base_date}, offset={offset})")
                        pass
                    return ""
                
            except (KeyError, FileNotFoundError, pd.errors.EmptyDataError) as e:
                print(f"處理檔案時出錯: {file_name}, 錯誤: {e}")
                continue
    
    # CHANGED: Updated the check for non-trading days at end of function
    from datetime import timedelta
    target_date = base_date + timedelta(days=offset)
    is_weekend = target_date.weekday() >= 5
    is_holiday = target_date in holidays_set  # NEW
    is_non_trading_day = is_weekend or is_holiday  # NEW
    
    if not is_non_trading_day:  # CHANGED from "if target_date.weekday() < 5:"
        print(f"無資料: security_id={security_id}, target_date={target_date} (base_date={base_date}, offset={offset})")
    return ""

# 3. 計算資料總數與總工作天數
def get_security_stats(security_id):
    """
    計算資料總數與總工作天數
    """
    for file_name in all_files:
        if file_name.startswith(f"[{security_id}]") and file_name.endswith(".csv"):
            try:
                # Update file path to use stockdata directory
                full_path = os.path.join('stockdata', file_name)
                price_data = pd.read_csv(full_path, encoding='utf-8')

                total_rows = price_data.shape[0]
                price_data['日期'] = pd.to_datetime(price_data['日期'], errors='coerce').dt.date

                match = re.search(r"\[(\d+)\] (\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})", file_name)
                if match:
                    start_date = pd.to_datetime(match.group(2), errors='coerce').date()
                    end_date = pd.to_datetime(match.group(3), errors='coerce').date()

                    if start_date and end_date:
                        working_days = 0
                        current_date = start_date
                        while current_date <= end_date:
                            if not cal.is_holiday(current_date) and current_date not in holidays_set and cal.is_working_day(current_date):
                                working_days += 1
                            current_date += timedelta(days=1)

                        print(f"股票代號: {security_id}, 資料總數: {total_rows}/總工作天數: {working_days}")
                        return total_rows, working_days
                    else:
                        return total_rows, "無資料"
                else:
                    return total_rows, "無資料"

            except (FileNotFoundError, pd.errors.EmptyDataError) as e:
                print(f"讀取證券檔案錯誤: {e}")
                return "無資料", "無資料"
    return "無資料", "無資料"


# 4. 更新資料中的日期欄位並添加新列
auction_data.insert(auction_data.columns.get_loc("DateEnd") + 1, "資料總數", "無資料")
auction_data.insert(auction_data.columns.get_loc("資料總數") + 1, "總工作天數", "無資料")

for index, row in auction_data.iterrows():
    security_id = row["股票代號"]

    # 更新日期欄位，根據偏移量調整收盤價查詢
    for col, info in date_columns.items():
        base_col = info['base']
        offset = info['offset']

        if base_col in auction_data.columns and pd.notna(row[base_col]):
            closing_price = get_closing_price(security_id, row[base_col], offset)
            auction_data.at[index, col] = closing_price
        else:
            auction_data.at[index, col] = "無資料"


    
    # 獲取資料總數和總工作天數
    total_rows, working_days = get_security_stats(security_id)
    auction_data.at[index, "資料總數"] = total_rows
    auction_data.at[index, "總工作天數"] = working_days

# 5. 儲存更新的資料至新的檔案中
output_path = os.path.join(output_dir, "updated_cleaned_auction_data.csv")
auction_data.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"已完成資料處理並儲存至 {output_path}")
