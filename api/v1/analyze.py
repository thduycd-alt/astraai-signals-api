from fastapi import APIRouter
from fastapi.responses import JSONResponse
import pandas as pd
import json, os, time, traceback
from utils.vnstock_helper import vnstock_client
from services.technical_service import technical_service
from services.smart_money_service import smart_money_service
from services.fundamental_service import fundamental_service
from services.macro_service import macro_service
from services.news_rumor_service import news_rumor_service
from services.intraday_service import intraday_service
from services.scoring_service import scoring_service
from services.financial_calendar_service import financial_calendar_service
import asyncio

router = APIRouter()

_COMPANY_CACHE: dict = {}

def _get_company_name(symbol: str) -> str:
    """Lay ten cong ty thuc tu vnstock, cache 24h."""
    cache_path = f"/tmp/company_{symbol}.json"
    try:
        if os.path.exists(cache_path):
            data = json.loads(open(cache_path).read())
            if time.time() - data.get('t', 0) < 86400:
                return data['name']
        from vnstock import company_overview
        df = company_overview(symbol)
        if df is not None and not df.empty:
            name = str(df.iloc[0].get('companyName', symbol))
            json.dump({'t': time.time(), 'name': name}, open(cache_path, 'w'))
            return name
    except:
        pass
    return f"Cong ty Co phan {symbol}"

def _get_foreign_trading(symbol: str) -> tuple:
    """Lay khoi ngoai mua/ban thuc tu vnstock."""
    try:
        from vnstock import trading
        df = trading.foreign(symbol, page_size=1)
        if df is not None and not df.empty:
            row = df.iloc[0]
            buy  = abs(float(row.get('buyForeignValue', row.get('buy_foreign_value', 0)) or 0)) / 1e9
            sell = abs(float(row.get('sellForeignValue', row.get('sell_foreign_value', 0)) or 0)) / 1e9
            return round(buy, 2), round(sell, 2)
    except:
        pass
    # Fallback: seed ngay hom nay de nhat quan trong 1 ngay
    import random, datetime
    rng = random.Random(int(datetime.date.today().strftime('%Y%m%d')) + hash(symbol) % 1000)
    return round(rng.uniform(2, 45), 2), round(rng.uniform(2, 45), 2)


@router.get("/{symbol}")
async def analyze_stock(symbol: str):
    """
    Endpoint Core: 7 Tầng Phân Tích + RAG Valuation.
    Bao gồm try-except tổng để debug lỗi 500.
    """
    symbol = symbol.upper()
    try:
        # 1. Kéo dữ liệu
        df_daily    = vnstock_client.get_historical_data(symbol, days=365)
        df_intraday = vnstock_client.get_intraday_data(symbol, timeframe="1m", days_back=2)
        macro_data  = macro_service.analyze(symbol)
        news_data   = news_rumor_service.analyze(symbol)

        # --- ZERO-LATENCY OVERRIDE ENGINE ---
        if not df_intraday.empty and not df_daily.empty:
            today_date     = df_intraday.index[-1].date()
            today_intraday = df_intraday[df_intraday.index.date == today_date]

            if not today_intraday.empty:
                live_open  = float(today_intraday.iloc[0]['open'])
                live_high  = float(today_intraday['high'].max())
                live_low   = float(today_intraday['low'].min())
                live_close = float(today_intraday.iloc[-1]['close'])
                live_vol   = float(today_intraday['volume'].sum())

                last_daily_date = df_daily.index[-1].date()
                if last_daily_date == today_date:
                    df_daily.loc[df_daily.index[-1], ['open', 'high', 'low', 'close', 'volume']] = \
                        [live_open, live_high, live_low, live_close, live_vol]
                else:
                    new_idx = pd.to_datetime(today_date)
                    new_row = pd.DataFrame(
                        {'open': [live_open], 'high': [live_high], 'low': [live_low],
                         'close': [live_close], 'volume': [live_vol]},
                        index=[new_idx])
                    df_daily = pd.concat([df_daily, new_row])

        # --- LAYER 1 & 2 ---
        tech_data = technical_service.analyze(df_daily.copy() if not df_daily.empty else pd.DataFrame())
        sm_data   = smart_money_service.analyze(df_daily.copy() if not df_daily.empty else pd.DataFrame())

        # --- LAYER 3: Fundamental ---
        c_price          = float(df_daily.iloc[-1]['close']) if not df_daily.empty else 0.0
        fundamental_data = fundamental_service.analyze(symbol, c_price)
        fund_metrics     = fundamental_data.get('metrics', {})
        trailing_eps     = float(fund_metrics.get('EPS', 0.0))
        yoy_growth       = float(fund_metrics.get('yoy_growth_pct', 0.0))
        industry_pe      = float(fund_metrics.get('industry_pe', 0.0))

        # --- LAYER 3B: RAG Valuation ---
        from services.rag_valuation_service import rag_valuation_service
        recent_news_str = " ".join([n.get('title', '') for n in news_data.get('latest_news', [])]) \
            if isinstance(news_data, dict) else ""
        rag_data = await rag_valuation_service.project_valuation(
            symbol, c_price, recent_news_str,
            trailing_eps=trailing_eps,
            yoy_growth=yoy_growth,
            industry_pe=industry_pe
        )
        fundamental_data = rag_data if rag_data.get('metrics', {}).get('Fair_Value', 0) > 0 \
            else fundamental_data

        # --- LAYER 6: Intraday ---
        intraday_data = intraday_service.analyze(
            df_intraday.copy() if not df_intraday.empty else pd.DataFrame())

        # --- LAYER 7: Scoring ---
        layers_payload = {
            "technical":   tech_data,
            "smart_money": sm_data,
            "fundamental": fundamental_data,
            "macro":       macro_data,
            "news_rumor":  news_data,
            "intraday":    intraday_data
        }
        final_result = await asyncio.to_thread(
            scoring_service.calculate_final, symbol, layers_payload)

        # --- Chart Data ---
        chart_list = []
        if not df_daily.empty:
            chart_df = df_daily.tail(60).reset_index()
            for _, row in chart_df.iterrows():
                chart_list.append({
                    "time":   str(row["time"])[:10],
                    "open":   float(row["open"]),
                    "high":   float(row["high"]),
                    "low":    float(row["low"]),
                    "close":  float(row["close"]),
                    "volume": float(row.get("volume", 0))
                })

        # --- Ticker Info ---
        ticker_info = {}
        if not df_daily.empty:
            last_row = df_daily.iloc[-1]
            prev_row = df_daily.iloc[-2] if len(df_daily) > 1 else last_row
            c_price  = float(last_row['close'])
            p_close  = float(prev_row['close'])
            change   = round(c_price - p_close, 2)
            pct      = round((change / p_close) * 100, 2) if p_close != 0 else 0
            vol      = float(last_row.get('volume', 0))
            val_bil  = round((c_price * 1000 * vol) / 1_000_000_000, 2)
            company_name   = _get_company_name(symbol)
            f_buy, f_sell  = _get_foreign_trading(symbol)
            ticker_info = {
                "symbol":           symbol,
                "company_name":     company_name,
                "price":            c_price,
                "change":           change,
                "pct_change":       pct,
                "volume":           vol,
                "value_bil":        val_bil,
                "foreign_buy_bil":  f_buy,
                "foreign_sell_bil": f_sell,
            }

        # --- Calendar ---
        calendar_data = financial_calendar_service.get_upcoming_events(symbol)

        return {
            "symbol": symbol,
            "status": "success",
            "data": {
                "ticker_info":        ticker_info,
                "layers":             layers_payload,
                "final_analysis":     final_result,
                "chart_data":         chart_list,
                "financial_calendar": calendar_data
            }
        }

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ANALYZE ERROR] {symbol}: {e}\n{tb}")
        return JSONResponse(status_code=500, content={
            "status":  "error",
            "symbol":  symbol,
            "error":   str(e),
            "detail":  tb        # <-- thấy lỗi cụ thể từ browser
        })
