import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class IntradayService:
    """
    Layer 6: Intraday Signals (Trọng số 10%)
    Dò Local Bottoms (Vùng Mua) và Local Tops (Vùng Bán).
    Khung thời gian siêu ngắn: 1m, 3m, 5m.
    Sử dụng scipy.signal.argrelextrema và Cumulative Volume Delta (CVD).
    """

    @staticmethod
    def analyze(df: pd.DataFrame, order: int = 5) -> dict:
        """
        order: Số nến hai bên để xác nhận 1 đỉnh/đáy cục bộ.
        """
        if df is None or df.empty or len(df) < 20:
            return {"error": "Not enough intraday data", "score": 50}

        try:
            prices = df['close'].values
            
            # Tìm Local Maxima (Đỉnh) và Local Minima (Đáy) bằng Scipy
            local_max_idx = argrelextrema(prices, np.greater, order=order)[0]
            local_min_idx = argrelextrema(prices, np.less, order=order)[0]

            # Khoảng cách từ nến hiện tại đến đỉnh/đáy gần nhất
            latest_idx = len(prices) - 1
            distance_to_last_bottom = latest_idx - (local_min_idx[-1] if len(local_min_idx) > 0 else 0)
            distance_to_last_top = latest_idx - (local_max_idx[-1] if len(local_max_idx) > 0 else 0)

            # Tính Cumulative Volume Delta (CVD) - Đo lường áp lực Mua/Bán chủ động
            current_close = df['close']
            prev_close = df['close'].shift(1)
            
            # Gán dấu cho Volume (1 nếu nến xanh, -1 nếu nến đỏ)
            vol_sign = np.where(current_close > prev_close, 1, 
                       np.where(current_close < prev_close, -1, 0))
            
            df['CVD'] = (df['volume'] * vol_sign).cumsum()
            cvd_latest = df['CVD'].iloc[-1]
            cvd_prev = df['CVD'].iloc[-2] if len(df) > 1 else 0
            
            cvd_trend = "Accumulating (Gom hàng)" if cvd_latest > cvd_prev else "Distributing (Xả hàng)"

            # Chấm điểm Intraday (0-100)
            score = 50
            signal = "Neutral (Đi ngang)"

            # Nếu nến hiện tại rất gần Đáy cục bộ (<= 3 nến) + CVD Gom hàng -> Báo Mua
            if distance_to_last_bottom <= 3 and cvd_trend == "Accumulating (Gom hàng)":
                signal = "Buy Zone (Local Bottom Detected)"
                score += 35 # Cộng mạnh
            # Nếu nến hiện tại sát Đỉnh cục bộ + CVD Xả hàng -> Báo Bán
            elif distance_to_last_top <= 3 and cvd_trend == "Distributing (Xả hàng)":
                signal = "Sell Zone (Local Top Detected)"
                score -= 35 # Trừ mạnh
            else:
                if cvd_trend == "Accumulating (Gom hàng)": score += 10
                else: score -= 10

            return {
                "score": max(0, min(100, score)),
                "signal": signal,
                "metrics": {
                    "distance_to_last_bottom_candles": int(distance_to_last_bottom),
                    "distance_to_last_top_candles": int(distance_to_last_top),
                    "cumulative_volume_delta": "Positive" if cvd_latest > 0 else "Negative",
                    "cvd_trend": cvd_trend
                }
            }
            
        except Exception as e:
            print(f"Intraday Analysis Error: {e}")
            return {"error": str(e), "score": 50}

intraday_service = IntradayService()
