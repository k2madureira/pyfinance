from collections import deque
from datetime import datetime
import pytz
from django.utils import timezone

COLORS = {
    'RESET': '\033[0m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
}

def colorize_text(text, color_code):
    return f"{color_code}{text}{COLORS['RESET']}"



def console_log(title, str):
  return print(colorize_text(f'{title}:', COLORS['YELLOW']),colorize_text(f'{str}', COLORS['BLUE']))

def console_error(title, str):
  return print(colorize_text(f'{title}:', COLORS['RED']),colorize_text(f'{str}', COLORS['YELLOW']))


def get_sma_days(sma):
    sma_days_default = 3
    sma_days_str = sma

    if sma_days_str:
        try:
            sma_days = int(sma_days_str)   
            if sma_days <= 0:
                sma_days = sma_days_default
                print(f"Warning: sma_days must be a positive integer. Using default: {sma_days_default}")
        except ValueError: 
            sma_days = sma_days_default
            print(f"Warning: Invalid sma_days parameter '{sma_days_str}'. Using default: {sma_days_default}")
    else:
        sma_days = sma_days_default
    
    return sma_days





def detecting_splits(quotes: list):
    

    TOLERANCE = 0.01 # Margem de erro
    common_split_ratios = {
        "2:1": 1/2,
        "3:1": 1/3,
        "4:1": 1/4,
        "5:1": 1/5,
        "6:1": 1/6,
        "7:1": 1/7,
        "10:1": 1/10,
        "20:1": 1/20,
        "1:2": 2/1,
        "1:3": 3/1,
        "1:4": 4/1,
        "1:5": 5/1,
        "1:10": 10/1,
    }

    splits_detected = []
    for i in range(len(quotes) - 1):
        current_quote = quotes[i]
        previous_quote = quotes[i+1]
        try:
            current_price = float(current_quote['close_price'])
            previous_price = float(previous_quote['close_price'])

            if previous_price <= 0:
                continue

            ratio = current_price / previous_price
            for split_type, split_ratio_expected in common_split_ratios.items():

              
                if abs(ratio - split_ratio_expected) < TOLERANCE:
                    splits_detected.append({
                        **current_quote,
                        "split_type": split_type,
                        "previous_price": previous_price,
                        "ratio": ratio
                    })
                    break 

        except ValueError:
            console_error('Warning', f"Unable to convert close_price to number in dates{current_quote['date']} ou {previous_quote['date']}")
        except Exception as e:
            console_error('Error', f"{e}")
        
    return splits_detected

def atypical_volume(quotes: list, sma_days_volume: int, threshold: float):
    quotes = sorted(quotes, key=lambda quote: quote['date'])

    volume_historic = deque()
    volume_atypical = []

    for i, quote in enumerate(quotes):
        current_volume = quote['volume']
        volume_historic.append(current_volume)

        if len(volume_historic) > sma_days_volume:
            volume_historic.popleft()

        if len(volume_historic) == sma_days_volume:
            sma_volume = sum(volume_historic) / sma_days_volume

            if current_volume > sma_volume * threshold:
                volume_atypical.append({
                    **quote,
                    "sma_volume": round(sma_volume),
                    "reason": f"Volume {current_volume} > {threshold}x SMA ({round(sma_volume)})"
                })

    return volume_atypical

def rsi(quotes: list, period:int):
    
    if len(quotes) < period + 1:
        console_error('Insuficient data', f"Min: {period + 1} days")
        return quotes
    
    quotes = sorted(quotes, key=lambda quote: quote['date'])
    gains = []
    losses = []

    for i in range(1, len(quotes)):
        current_price = float(quotes[i]['close_price'])
        previous_price = float(quotes[i-1]['close_price'])
        
        change = current_price - previous_price
        
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    initial_gains = gains[:period]
    initial_losses = losses[:period]

    avg_gain = sum(initial_gains) / period
    avg_loss = sum(initial_losses) / period

  
    rsi_values = [None] * period

    if avg_loss == 0:
        rsi = 100 
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    rsi_values.append(rsi)

    for i in range(period, len(gains)):
       
        current_gain = gains[i]
        current_loss = losses[i]

        avg_gain = ((avg_gain * (period - 1)) + current_gain) / period
        avg_loss = ((avg_loss * (period - 1)) + current_loss) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    rsi_quotes = []
    for i, quote in enumerate(quotes):
        if i >= 2:
            rsi_quotes.append({
                **quotes[i],
                "rsi": rsi_values[i],
            })
        else:
            rsi_quotes.append({
                **quotes[i],
                "rsi": None,
            }) 

    return rsi_quotes

def quotes_by_date(quotes: list, start_date, end_date):
    try:
        if start_date and not start_date.tzinfo:
            start_date = timezone.make_aware(start_date, pytz.utc)
        elif start_date and start_date.tzinfo != pytz.utc:
            start_date = start_date.astimezone(pytz.utc)

        if end_date and not end_date.tzinfo:
            end_date = timezone.make_aware(end_date, pytz.utc)
        elif end_date and end_date.tzinfo != pytz.utc:
            end_date = end_date.astimezone(pytz.utc)
    
        filtered_quotes = []
        for quote in quotes:
            try:
                quote_date_str = quote.get('date')
                temp_quote_dt = datetime.fromisoformat(quote_date_str.replace('Z', '+00:00'))
                    
                if temp_quote_dt.tzinfo: 
                    quote_date = temp_quote_dt.astimezone(pytz.utc)
                else: 
                    quote_date = timezone.make_aware(temp_quote_dt, pytz.utc)
             
                if start_date <= quote_date <= end_date:
                    filtered_quotes.append(quote)
                    
            except ValueError:
                console_error('Invalid format', f"must use format 'AAAA-MM-DD'")
                continue
            except KeyError:
                console_error('Invalid key', f"quote without date field")
                continue
                
        return filtered_quotes

    except ValueError:
        console_error('Invalid date', f"must use format 'AAAA-MM-DD'")
        return []