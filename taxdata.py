from datetime import datetime
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
    def __init__(self, date:datetime, type, group,
                 buy_coin, buy_amount, buy_value,
                 sell_coin, sell_amount, sell_value):
        self.date = date
        self.type = type
        self.group = group
        self.buy_coin = buy_coin
        self.buy_amount = buy_amount
        self.buy_value = buy_value
        self.sell_coin = sell_coin
        self.sell_amount = sell_amount
        self.sell_value = sell_value


class Trades:
    def __init__(self, trades):
        self.trades = trades

    @staticmethod
    def read_from(filename):
        with open(filename, encoding='utf-8-sig') as f:
            lines = [line for line in csv.reader(f, delimiter=',', quotechar='"')]

        def indices(col_name):
            return [index for index, col in enumerate(lines[0]) if col == col_name]

        date_index = indices('Date')[0]
        type_index = indices('Type')[0]
        group_index = indices('Group')[0]
        buy_coin_index = indices('Cur.')[0]
        buy_amount_index = indices('Buy')[0]
        buy_value_index = indices('Value in SEK')[0]
        sell_coin_index = indices('Cur.')[1]
        sell_amount_index = indices('Sell')[0]
        sell_value_index = indices('Value in SEK')[1]

        trades = []
        for line in lines[1:]:
            trades.append(Trade(
                datetime.strptime(line[date_index], "%d.%m.%Y %H:%M"),
                line[type_index],
                None if line[group_index] == '-' else line[group_index],
                None if line[buy_coin_index] == '-' else line[buy_coin_index],
                None if line[buy_amount_index] == '-' else float(line[buy_amount_index]),
                None if line[buy_value_index] == '-' else float(line[buy_value_index]),
                None if line[sell_coin_index] == '-' else line[sell_coin_index],
                None if line[sell_amount_index] == '-' else float(line[sell_amount_index]),
                None if line[sell_value_index] == '-' else float(line[sell_value_index])
            ))

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
