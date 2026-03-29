import pandas as pd
import pandas_ta as ta

class SmartMoneyService:
    """
    Layer 2: Dòng Tiền & Smart Money Footprints (Trọng số 25%)
    Chỉ báo VSA & Volume: OBV, Chaikin Money Flow (CMF), Khối lượng đột biến > 3 lần TB 20 phiên.
    """

    @staticmethod
    def analyze(df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 20:
            return {"error": "Not enough data for volume analysis", "score": 0}

        try:
            # 1. OBV (On Balance Volume) - Áp lực Mua/Bán tích lũy
            df.ta.obv(append=True)
            
            # 2. CMF (Chaikin Money Flow) - Mặc định window = 20
            df.ta.cmf(append=True)
            
            # 3. Tính toán Volume Trung bình 20 phiên
            df['VOL_SMA_20'] = df['volume'].rolling(window=20).mean()

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # Logic 1: OBV Trend
            obv = latest.get('OBV', 0)
            obv_prev = prev.get('OBV', 0)
            obv_trend = "Accumulation (Mua Gom)" if obv > obv_prev else "Distribution (Bán Xả)"

            # Logic 2: CMF Status
            cmf = latest.get('CMF_20', 0)
            if cmf > 0.05:
                cmf_status = "Lực Cầu Mạnh (Dòng tiền lớn vào)"
            elif cmf < -0.05:
                cmf_status = "Lực Xả Mạnh (Dòng tiền lớn thoát)"
            else:
                cmf_status = "Trung lập"

            # Logic 3: Đột biến Volume (Volume Anomaly > 3x Mức TB)
            vol_current = latest['volume']
            vol_sma20 = latest.get('VOL_SMA_20', vol_current)
            
            vol_anomaly = False
            vol_multiplier = 0.0
            if vol_sma20 > 0:
                vol_multiplier = vol_current / vol_sma20
                if vol_multiplier >= 3.0:  # Gấp 3 lần trung bình 20 ngày
                    vol_anomaly = True

            # 4. Tính toán Khối lượng Cá mập Gom/Xả ròng trong 15 phiên gần nhất
            df_recent = df.tail(15)
            shark_buy_vol = 0
            shark_sell_vol = 0
            
            for index, row in df_recent.iterrows():
                vol = row['volume']
                sma = row.get('VOL_SMA_20', vol)
                # Dấu chân cá mập: Khối lượng lớn hơn 1.25 lần trung bình là bắt đầu có tay to
                if sma > 0 and vol >= sma * 1.25: 
                    if row['close'] > row['open']:
                        shark_buy_vol += vol
                    else:
                        shark_sell_vol += vol
            
            net_shark_vol = float(shark_buy_vol - shark_sell_vol)

            # Hệ thống chấm điểm Smart Money (0-100)
            score = 50
            if obv_trend == "Accumulation (Mua Gom)": score += 10
            else: score -= 10
            
            if cmf > 0.1: score += 15
            elif cmf < -0.1: score -= 15
            
            # Yếu tố Khối lượng ròng quyết định xu hướng tay to
            if net_shark_vol > 0:
                score += 15
            elif net_shark_vol < 0:
                score -= 15

            # Nếu có khối lượng đột biến phiên nay (dấu tay To tham gia Tức thời)
            if vol_anomaly:
                if latest['close'] > latest['open']:
                    score += 10 # Đột biến khối lượng + nến tăng
                else:
                    score -= 10 # Đột biến khối lượng + nến giảm

            return {
                "score": max(0, min(100, score)),
                "obv_trend": obv_trend,
                "cmf": {
                    "value": round(cmf, 3) if pd.notna(cmf) else 0.0,
                    "status": cmf_status
                },
                "volume_analysis": {
                    "vol_multiplier": round(vol_multiplier, 2),
                    "is_anomaly_3x": vol_anomaly,
                    "net_shark_vol": net_shark_vol
                }
            }

        except Exception as e:
            print(f"Smart Money Analysis Error: {e}")
            return {"error": str(e), "score": 50}

smart_money_service = SmartMoneyService()
