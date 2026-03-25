import pandas as pd
import pandas_ta as ta

class TechnicalService:
    """
    Layer 1: Phân tích Kỹ Thuật thuần túy (Technical Analysis) - Trọng số 25%
    Chỉ báo tĩnh: RSI(14), MACD, Bollinger Bands(20,2), MA20/50/200, Pivot Points.
    """

    @staticmethod
    def analyze(df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 50:
            return {"error": "Not enough data (need at least 50 bars)", "score": 0}

        try:
            # 1. Moving Averages
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            if len(df) >= 200:
                df.ta.sma(length=200, append=True)

            # 2. RSI
            df.ta.rsi(length=14, append=True)

            # 3. MACD
            df.ta.macd(fast=12, slow=26, signal=9, append=True)

            # 4. Bollinger Bands
            df.ta.bbands(length=20, std=2, append=True)

            # Lấy nến hiện tại và nến trước đó
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            close_price = latest['close']

            # Đánh giá MA Trend (Ngắn hạn)
            ma20 = latest.get('SMA_20', close_price)
            ma50 = latest.get('SMA_50', close_price)
            
            trend = "Sideway"
            if close_price > ma20 and ma20 > ma50:
                trend = "Uptrend Short-term"
            elif close_price < ma20 and ma20 < ma50:
                trend = "Downtrend Short-term"

            # Đánh giá sức mạnh RSI
            rsi = latest.get('RSI_14', 50)
            rsi_status = "Neutral"
            if rsi > 70:
                rsi_status = "Overbought"
            elif rsi < 30:
                rsi_status = "Oversold"

            # Đánh giá giao cắt MACD
            macd_line = latest.get('MACD_12_26_9', 0)
            signal_line = latest.get('MACDs_12_26_9', 0)
            macd_status = "Bullish (Tăng)" if macd_line > signal_line else "Bearish (Giảm)"

            # Pivot Points (Sơ bộ dùng công thức Classic cho nến trước)
            pivot = (prev['high'] + prev['low'] + prev['close']) / 3
            r1 = (2 * pivot) - prev['low']
            s1 = (2 * pivot) - prev['high']

            # Hệ thống chấm điểm Kỹ Thuật (Scale 0-100)
            score = 50
            if rsi_status == "Oversold": score += 15 # Dễ bật nảy
            if rsi_status == "Overbought": score -= 15 # Dễ chỉnh xả
            
            if trend == "Uptrend Short-term": score += 20
            elif trend == "Downtrend Short-term": score -= 20
            
            if macd_status == "Bullish (Tăng)": score += 15
            else: score -= 15

            return {
                "score": max(0, min(100, score)),
                "trend": trend,
                "rsi": {
                    "value": round(rsi, 2),
                    "status": rsi_status
                },
                "macd": {
                    "status": macd_status,
                    "macd_hist": round(latest.get('MACDh_12_26_9', 0), 2)
                },
                "ma_status": {
                    "price_vs_ma20": "Above" if close_price > ma20 else "Below",
                },
                "pivot_points": {
                    "Pivot": round(pivot, 2),
                    "Resistance_1": round(r1, 2),
                    "Support_1": round(s1, 2)
                }
            }

        except Exception as e:
            print(f"Technical Analysis Error: {e}")
            return {"error": str(e), "score": 50}

technical_service = TechnicalService()
