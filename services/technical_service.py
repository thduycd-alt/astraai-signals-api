import pandas as pd
import pandas_ta as ta

class TechnicalService:
    """
    Layer 1: Phân tích Kỹ Thuật Chuyên Sâu (Technical Analysis V3) - Trọng số 25%
    Các chỉ báo: RSI(14), MACD, Bollinger Bands(20,2), MA20/50/200.
    Các mô hình Nâng cao: SMC (Order Blocks, Fakeout), Breakout, Pullback.
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

            # 2. RSI, MACD, BBands & Stochastic RSI
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.stochrsi(length=14, append=True)

            # Lấy nến hiện tại và nến trước đó
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            close_price = latest['close']
            
            # --- ÁP DỤNG CÁC MÔ HÌNH V3 ENTERPRISE ---
            # A. Xác định Xu Hướng Cốt Lõi (Core Trend)
            ma20 = latest.get('SMA_20', close_price)
            ma50 = latest.get('SMA_50', close_price)
            
            trend = "Sideway (Tích lũy chặt)"
            if close_price > ma20 and ma20 > ma50:
                trend = "Uptrend (Sóng tăng mạnh)"
            elif close_price < ma20 and ma20 < ma50:
                trend = "Downtrend (Sóng giảm chủ đạo)"

            # B. SMC (Smart Money Concepts) - Dò tìm Order Block
            # Dò tìm Nến Cường lực (Marubozu/Nến đặc)
            is_bullish_ob = False
            is_bearish_ob = False
            candle_body = abs(close_price - latest['open'])
            candle_range = latest['high'] - latest['low']
            if candle_range > 0 and (candle_body / candle_range) > 0.7: 
                # Nến rất đặc
                if close_price > latest['open']:
                    is_bullish_ob = True
                else:
                    is_bearish_ob = True
            
            smc_signal = "Không rõ ràng"
            if is_bullish_ob and trend != "Downtrend (Sóng giảm chủ đạo)":
                smc_signal = "Bullish Order Block (Điểm nổ của Cá mập)"
            elif is_bearish_ob and trend != "Uptrend (Sóng tăng mạnh)":
                smc_signal = "Bearish Order Block (Cây nến Phân phối)"

            # C. Breakout & Pullback Analysis
            highest_20 = df['high'].rolling(20).max().iloc[-2]
            lowest_20 = df['low'].rolling(20).min().iloc[-2]
            
            action_pattern = "Đi ngang trong biên độ"
            if close_price > highest_20:
                action_pattern = "Breakout Đỉnh 20 phiên"
            elif close_price < lowest_20:
                action_pattern = "Thủng Đáy 20 phiên (Cắt lỗ dứt khoát)"
            elif trend == "Uptrend (Sóng tăng mạnh)" and latest['low'] <= ma20 and close_price > ma20:
                action_pattern = "Pullback Đẹp (Rũ bỏ về đường hỗ trợ MA20 và Rút chân)"

            # --- PHÁT HIỆN PHÂN KỲ RSI (Divergence — Tín Hiệu Đảo Chiều Mạnh) ---
            rsi = latest.get('RSI_14', 50)
            rsi_series = df['RSI_14'].dropna()
            price_series = df['close']
            divergence_signal = "Không có phân kỳ"
            if len(rsi_series) >= 10:
                # Bearish Divergence: Giá tăng đỉnh mới nhưng RSI tạo đỉnh thấp hơn → sắp giảm
                if price_series.iloc[-1] > price_series.iloc[-5] and rsi_series.iloc[-1] < rsi_series.iloc[-5]:
                    divergence_signal = "⚠️ Phân Kỳ Âm (Bearish Divergence): Giá tăng đỉnh mới, RSI suy yếu — nguy cơ đảo chiều"
                # Bullish Divergence: Giá tạo đáy mới nhưng RSI tạo đáy cao hơn → sắp tăng
                elif price_series.iloc[-1] < price_series.iloc[-5] and rsi_series.iloc[-1] > rsi_series.iloc[-5]:
                    divergence_signal = "✅ Phân Kỳ Dương (Bullish Divergence): Giá giảm đáy mới, RSI hồi phục — tín hiệu bắt đáy"

            stoch_k = latest.get('STOCHRSIk_14_14_3_3', 50)
            stoch_d = latest.get('STOCHRSId_14_14_3_3', 50)

            # --- TÍNH ĐIỂM SỐ CHUYÊN MÔN ---
            macd_line = latest.get('MACD_12_26_9', 0)
            signal_line = latest.get('MACDs_12_26_9', 0)
            
            score = 50
            if trend == "Uptrend (Sóng tăng mạnh)": score += 15
            elif trend == "Downtrend (Sóng giảm chủ đạo)": score -= 15
            
            if rsi < 30: score += 10 # Quá bán, rủi ro thấp
            elif rsi > 70: score -= 10 # Quá mua, rủi ro cao chỉnh
            
            if macd_line > signal_line: score += 10
            else: score -= 10
            
            if action_pattern == "Breakout Đỉnh 20 phiên": score += 15
            elif action_pattern == "Pullback Đẹp (Rũ bỏ về đường hỗ trợ MA20 và Rút chân)": score += 10
            elif "Thủng Đáy" in action_pattern: score -= 15
            
            if smc_signal == "Bullish Order Block (Điểm nổ của Cá mập)": score += 10
            elif "Bearish" in smc_signal: score -= 10

            # RSI Divergence — Tín hiệu đảo chiều mạnh
            if "Bearish Divergence" in divergence_signal: score -= 15
            elif "Bullish Divergence" in divergence_signal: score += 15

            # Stochastic RSI xác nhận
            if pd.notna(stoch_k) and pd.notna(stoch_d):
                if stoch_k > 80 and stoch_d > 80: score -= 5  # Vùng quá mua
                elif stoch_k < 20 and stoch_d < 20: score += 5  # Vùng quá bán

            return {
                "score": max(0, min(100, score)),
                "trend": trend,
                "smc_signal": smc_signal,
                "price_action_setup": action_pattern,
                "divergence_signal": divergence_signal,
                "indicators": {
                    "rsi_14": round(rsi, 2),
                    "stoch_rsi_k": round(float(stoch_k), 2) if pd.notna(stoch_k) else 50.0,
                    "macd_status": "Giao cắt Mua" if macd_line > signal_line else "Giao cắt Bán",
                    "price_vs_ma20": "Nằm Trên Hỗ Trợ" if close_price > ma20 else "Nằm Dưới Kháng Cự"
                }
            }

        except Exception as e:
            print(f"Technical Analysis Error: {e}")
            return {"error": str(e), "score": 50}

technical_service = TechnicalService()
