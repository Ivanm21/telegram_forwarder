import cryptocompare


def get_price_in_eur(coin):
    currency = 'EUR'
    coin = coin.upper()
    price = cryptocompare.get_price(coin, curr=currency)

    if price is None:
        return -1 
    else: 
        return float(price.get(coin).get(currency))

