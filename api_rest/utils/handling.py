
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
