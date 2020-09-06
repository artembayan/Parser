def clean_price(text):
    digits = [ symbol for symbol in text if symbol.isdigit() ]
    cleaned_price = ''.join(digits)
    if not cleaned_price:
        return None
    return cleaned_price

raw_current_price = 'ff5550'
# Очистка цены от посторонних элементов
current = clean_price(raw_current_price)
current_price = float(current) / (10 ** len(current))

raw_orginal_price = '11100tt'
original = clean_price(raw_orginal_price)
original_price = float(original) / (10 ** len(original))

sale_tag = "Скидка " + str(int(100 - ((int(current) / int(original))) * 100)) + "%"

print(current_price)
print(original_price)
print(sale_tag)