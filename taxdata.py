from datetime import datetime
import dateutil.parser
import csv
import json


class PersonalDetails:
    def __init__(self, namn, personnummer, postnummer, postort):
        self.namn = namn
        self.personnummer = personnummer
        self.postnummer = postnummer
        self.postort = postort

    @staticmethod
    def read_from(filename):
        with open(filename, encoding="utf-8-sig") as f:
            d = json.load(f)
            return PersonalDetails(d["namn"], d["personnummer"], d["postnummer"], d["postort"])


class Fees:
    def __init__(self, fees):
        self.fees = fees

    @staticmethod
    def read_from(filename):
        with open(filename, encoding="utf-8-sig") as f:
            d = json.load(f)
            return Fees(d["fees"])


class Trade:
    def __init__(self, lineno, date:datetime, type, group,
                 buy_coin, buy_amount, buy_value,
                 sell_coin, sell_amount, sell_value):
        self.lineno = lineno
        self.date = date
        self.type = type
        self.group = group
        self.buy_coin = buy_coin
        self.buy_amount = buy_amount
        self.buy_value = buy_value
        self.sell_coin = sell_coin
        self.sell_amount = sell_amount
        self.sell_value = sell_value


def read_usdsek_rates():
    rates = []
    with open('data/rates/usdsek.csv', encoding='utf-8-sig') as f:
        is_first = True
        for row in csv.reader(f, delimiter=',', quotechar='"'):
            if is_first:
                is_first = False
                continue
            date = dateutil.parser.parse(row[0])
            close = float(row[1])
            rates.append([date, close])
    rates.sort(key=lambda rate: rate[0])
    return rates


def usd_to_sek(rates, wanted_date):
    prev_date = None
    prev_price = None
    for rate in rates:
        date = rate[0]
        price = rate[1]
        if prev_date and prev_date <= wanted_date and wanted_date < date:
            return prev_price
        prev_date = date
        prev_price = price
    raise Exception("Didn't find a USDSEK conversion rate for date %s" % wanted_date)


class Trades:
    def __init__(self, trades):
        self.trades = trades

    @staticmethod
    def read_from(filename, value_in_usd):
        with open(filename, encoding='utf-8-sig') as f:
            lines = [line for line in csv.reader(f, delimiter=',', quotechar='"')]

        if value_in_usd:
            usdsek = read_usdsek_rates()

        def indices(col_name):
            return [index for index, col in enumerate(lines[0]) if col == col_name]

        price_field_name = 'Value in USD' if value_in_usd else 'Value in SEK'

        date_index = indices('Date')[0]
        type_index = indices('Type')[0]
        group_index = indices('Group')[0]
        buy_coin_index = indices('Cur.')[0]
        buy_amount_index = indices('Buy')[0]
        buy_value_index = indices(price_field_name)[0]
        sell_coin_index = indices('Cur.')[1]
        sell_amount_index = indices('Sell')[0]
        sell_value_index = indices(price_field_name)[1]

        trades = []
        lineno = 2
        for line in lines[1:]:
            trade = Trade(
                lineno,
                datetime.strptime(line[date_index], "%d.%m.%Y %H:%M"),
                line[type_index],
                None if line[group_index] == '-' else line[group_index],
                None if line[buy_coin_index] == '-' else line[buy_coin_index],
                None if line[buy_amount_index] == '-' else float(line[buy_amount_index]),
                None if line[buy_value_index] == '-' else float(line[buy_value_index]),
                None if line[sell_coin_index] == '-' else line[sell_coin_index],
                None if line[sell_amount_index] == '-' else float(line[sell_amount_index]),
                None if line[sell_value_index] == '-' else float(line[sell_value_index])
            )
            if value_in_usd:
                usdsek_rate = usd_to_sek(usdsek, trade.date)
                if trade.buy_value:
                    trade.buy_value *= usdsek_rate
                if trade.sell_value:
                    trade.sell_value *= usdsek_rate
            trades.append(trade)
            lineno += 1

        trades.reverse()
        trades.sort(key=lambda x: x.date)

        return Trades(trades)


class TaxEvent:
    def __init__(self, amount, name:str, income, cost):
        self.amount = amount
        self.name = name
        self.income = income
        self.cost = cost

    @staticmethod
    def headers():
        return ['Amount', 'Name', 'Income', 'Cost']

    def fields(self) -> []:
        return [self.amount, self.name, self.income, self.cost]

    def k4_fields(self) -> []:
        return [self.amount, self.name, self.income, self.cost,
                self.profit() if self.profit() > 0 else None,
                -self.profit() if self.profit() < 0 else None]

    def profit(self):
        return self.income - self.cost

    @staticmethod
    def read_stock_tax_events_from(filename:str):
        with open(filename, encoding="utf-8-sig") as f:
            d = json.load(f)
            events = []
            for event in d["trades"]:
                events.append(TaxEvent(event["amount"], event["name"], event["income"], event["costbase"]))
            return events


class TradeEvent:
    def __init__(self, date, name, amount, price, total_amount_before, total_amount_after, cost_basis_before, cost_basis_after, tax_event, trade_type):
        self.date = date
        self.name = name
        self.amount = amount
        self.price = price
        self.total_amount_before = total_amount_before
        self.total_amount_after = total_amount_after
        self.cost_basis_before = cost_basis_before
        self.cost_basis_after = cost_basis_after
        self.tax_event = tax_event
        self.trade_type = trade_type
