import random

def signal_sma(symbol: str, fast: int = 5, slow: int = 20):
    # Señal fake estable para que la API responda sin fallar
    last = 100.0
    sma_fast = 100.0 + random.uniform(-1, 1)
    sma_slow = 100.0 + random.uniform(-1, 1)
    if sma_fast > sma_slow:
        sig = "buy"
    elif sma_fast < sma_slow:
        sig = "sell"
    else:
        sig = "hold"
    return sig, {"last": last, "sma_fast": sma_fast, "sma_slow": sma_slow}

