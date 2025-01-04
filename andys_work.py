"""import os
import pandas as pd

def update_auction_data():
    input_file = "cleaned_auction_data.csv"
    output_dir = "updated_data"
    os.makedirs(output_dir, exist_ok=True)

    # 讀取主檔案
    auction_data = pd.read_csv(input_file)
    date_columns = [
        "申請日期",
        "上櫃審議委員會審議日期",
        "櫃買董事會通過上櫃日期",
        "櫃買同意上櫃契約日期",
        "投標開始日(T-4)",
        "投標結束日(T-2)",
        "開標日期(T)",
        "撥券日(上市上櫃日) T+7"
    ]

    # 處理每一個證券代號
    for index, row in auction_data.iterrows():
        security_id = row['證券代號']
        relevant_file = None

        # 搜索對應的收盤價檔案
        for file_name in os.listdir():
            if file_name.startswith(f"[{security_id}]") and file_name.endswith(".csv"):
                relevant_file = file_name
                break

        if not relevant_file:
            print(f"未找到對應的收盤價檔案：{security_id}")
            continue

        # 讀取收盤價資料
        closing_data = pd.read_csv(relevant_file)
        if '收盤價' not in closing_data.columns or '日期' not in closing_data.columns:
            print(f"收盤價檔案缺少必要欄位：{relevant_file}")
            continue

        closing_data['日期'] = pd.to_datetime(closing_data['日期'])
        closing_price_map = dict(zip(closing_data['日期'].dt.date, closing_data['收盤價']))

        # 替換日期為收盤價
        for col in date_columns:
            if col in row and pd.notnull(row[col]):
                try:
                    date = pd.to_datetime(row[col]).date()
                    auction_data.at[index, col] = closing_price_map.get(date, "無收盤價")
                except Exception as e:
                    print(f"日期轉換錯誤於 {security_id}, 欄位 {col}: {e}")

    # 儲存處理後的檔案
    output_file = os.path.join(output_dir, "updated_auction_data.csv")
    auction_data.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"更新後的檔案已儲存至 {output_file}")

if __name__ == "__main__":
    update_auction_data()"""











      


















import os
import pandas as pd

# 設定資料夾名稱
output_folder = "updated_auction_data"
os.makedirs(output_folder, exist_ok=True)

# 讀取 cleaned_auction_data.csv
auction_data_path = "cleaned_auction_data.csv"
auction_data = pd.read_csv(auction_data_path)

# 更新收盤價的邏輯
for index, row in auction_data.iterrows():
   # if index < 2 or index > 9:  # 只處理第3到10行（從0開始計算）
        #continue
    
    # 取得證券代號，假設第一列名為 "證券代號"
    security_id = row["證券代號"]
    csv_file_pattern = f"[{security_id}]*.csv"
    
    # 在當前目錄中尋找符合模式的檔案
    matching_files = [f for f in os.listdir('.') if f.startswith(f"[{security_id}]") and f.endswith(".csv")]
    
    if not matching_files:
        print(f"未找到符合 {security_id} 的檔案")
        continue
    
    # 假設只有一個對應檔案
    closing_price_file = matching_files[0]
    closing_data = pd.read_csv(closing_price_file)
    
    # 確保含有 "收盤價" 列
    if "收盤價" not in closing_data.columns:
        print(f"檔案 {closing_price_file} 中未找到 '收盤價'")
        continue
    
    # 使用收盤價更新第3到10行
    auction_data.loc[index, auction_data.columns[2:10]] = closing_data["收盤價"].iloc[:8].values

# 將更新後的資料存入新檔案
updated_file_path = os.path.join(output_folder, "updated_cleaned_auction_data.csv")
auction_data.to_csv(updated_file_path, index=False, encoding="utf-8")
print(f"已將更新後的資料儲存至 {updated_file_path}")
