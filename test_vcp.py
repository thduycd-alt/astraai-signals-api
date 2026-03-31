import sys
import asyncio
import os

# Ensure the correct path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from api.v1.analyze import analyze_stock

async def print_val(symbol):
    print(f"\n--- Testing {symbol} ---")
    res = await analyze_stock(symbol)
    if 'data' in res and 'final_analysis' in res['data']:
        fund = res['data']['layers']['fundamental']['metrics']
        print(f"Fair Value Mid (Base): {fund.get('Fair_Value_Mid')}")
        print(f"Fair Value Low: {fund.get('Fair_Value_Low')}")
        print(f"Fair Value High: {fund.get('Fair_Value_High')}")
        print(f"PE Target: {fund.get('PE')}")
        print(f"Actual PE: {fund.get('actual_pe')}")
        print(f"Industry PE: {fund.get('industry_pe')}")
        print(f"Historical PE: {fund.get('hist_avg_pe')}")
        print(f"EPS: {fund.get('EPS')}")
        print(f"Actual PB: {fund.get('pb_actual')}")
        print(f"BVPS: {fund.get('book_value_per_share')}")
        print(f"AI Reasoning: {fund.get('AI_Reasoning')}")
        print(f"AI Expert Text:\n{res['data']['layers']['fundamental'].get('expert_text')}")
    else:
        print("Error or incomplete output:", res)

async def main():
    await print_val("HAG")
    await print_val("MBS")

if __name__ == "__main__":
    asyncio.run(main())
