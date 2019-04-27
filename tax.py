import os

from taxdata import TaxEvent, Trade, TradeEvent
from k4page import K4Section, K4Page


def is_fiat(coin):
    return coin in ["EUR", "USD", "SEK"]


class Coin:
    def __init__(self, symbol, max_overdraft, trade_events):
        self.symbol = symbol
        self.amount = 0.0
        self.cost_basis = 0.0
        self.max_overdraft = max_overdraft
        self.trade_events = trade_events

    def buy(self, amount:float, price:float, date, trade_type):
        new_amount = self.amount + amount
        new_cost_basis = (self.cost_basis * self.amount + price) / new_amount
        self.trade_events.append(TradeEvent(date, self.symbol, amount, price, self.amount, new_amount, self.cost_basis, new_cost_basis, None, trade_type))
        self.amount = new_amount
        self.cost_basis = new_cost_basis

    def sell(self, amount:float, price:float, date, trade_type:str) -> TaxEvent:
        amount_left = self.amount - amount
        if amount_left < -self.max_overdraft:
            raise Exception(f"Not enough coins available for {self.symbol}, {self.amount} < {amount}.")
        if amount_left < 0.0:
            amount_left = 0.0

        tax_event = TaxEvent(amount, self.symbol, price, self.cost_basis * amount)
        self.trade_events.append(TradeEvent(date, self.symbol, -amount, price, self.amount, amount_left, self.cost_basis, self.cost_basis, tax_event, trade_type))

        self.amount = amount_left

        return tax_event


def compute_tax(trades, from_date, to_date, max_overdraft, native_currency='SEK', exclude_groups=[], coin_report_filename=None):
    tax_events = []
    trade_events = []
    coins = {}

    def get_buy_coin(trade:Trade):
        if trade.buy_coin == native_currency:
            return None
        if trade.buy_coin not in coins:
            coins[trade.buy_coin] = Coin(trade.buy_coin, max_overdraft, trade_events)
        return coins[trade.buy_coin]

    def get_sell_coin(trade:Trade):
        if trade.sell_coin == native_currency:
            return None
        if trade.sell_coin not in coins:
            raise Exception(f"Selling currency {trade.sell_coin} which has not been bought yet")
        return coins[trade.sell_coin]

    for trade in trades.trades:
        if trade.date > to_date:
            break
        elif trade.group in exclude_groups:
            continue

        try:

            if trade.type == 'Trade':
                buy_coin = get_buy_coin(trade)
                sell_coin = get_sell_coin(trade)

                if trade.sell_coin == native_currency:
                    value_sek = trade.sell_value
                else:
                    value_sek = trade.buy_value

                if buy_coin:
                    buy_coin.buy(trade.buy_amount, value_sek, trade.date, trade.type)
                if sell_coin:
                    tax_event = sell_coin.sell(trade.sell_amount, value_sek, trade.date, trade.type)
                    if trade.date >= from_date:
                        tax_events.append(tax_event)

            elif trade.type == 'Mining':
                buy_coin = get_buy_coin(trade)
                if buy_coin:
                    buy_coin.buy(trade.buy_amount, trade.buy_value, trade.date, trade.type)

            elif trade.type == 'Gift/Tip':
                buy_coin = get_buy_coin(trade)
                if buy_coin:
                    buy_coin.buy(trade.buy_amount, 0.0, trade.date, trade.type)

            elif trade.type == 'Spend':
                sell_coin = get_sell_coin(trade)
                if sell_coin:
                    tax_event = sell_coin.sell(trade.sell_amount, trade.sell_value, trade.date, trade.type)
                    if trade.date >= from_date:
                        tax_events.append(tax_event)

        except Exception as e:
            print(f"Exception encountered at line {trade.lineno} in trades csv-file: {e}")
            return None

    if coin_report_filename:
        with open(coin_report_filename, "w") as f:
            f.write(f"{'Amount'.ljust(14)}{'Coin'.ljust(8)}{'Cost basis'.ljust(10)}\n")
            coin_list = [coin for (_, coin) in coins.items() if coin.amount > 1e-9]
            coin_list.sort(key=lambda coin: coin.symbol)
            for coin in coin_list:
                f.write(f"{str(coin.amount)[:12].ljust(14)}{str(coin.symbol).ljust(8)}{str(coin.cost_basis)[:8].ljust(10)}\n")

    return tax_events, trade_events


def aggregate_per_coin(tax_events):
    aggregate_tax_events = {}
    for tax_event in tax_events:
        if tax_event.name not in aggregate_tax_events:
            aggregate_tax_events[tax_event.name] = (TaxEvent(0.0, tax_event.name, 0.0, 0.0), TaxEvent(0.0, tax_event.name, 0.0, 0.0))
        (aggregate_profit_tax_event, aggregate_loss_tax_event) = aggregate_tax_events[tax_event.name]
        if tax_event.profit() > 0.0:
            aggregate_profit_tax_event.amount += tax_event.amount
            aggregate_profit_tax_event.income += tax_event.income
            aggregate_profit_tax_event.cost += tax_event.cost
        else:
            aggregate_loss_tax_event.amount += tax_event.amount
            aggregate_loss_tax_event.income += tax_event.income
            aggregate_loss_tax_event.cost += tax_event.cost

    sorted_aggregate_events = list(aggregate_tax_events.items())
    sorted_aggregate_events.sort()
    new_tax_events = []
    for (name, (aggregate_profit_tax_event, aggregate_loss_tax_event)) in sorted_aggregate_events:
        if (aggregate_profit_tax_event.amount > 0.0):
            new_tax_events.append(aggregate_profit_tax_event)
        if (aggregate_loss_tax_event.amount > 0.0):
            new_tax_events.append(aggregate_loss_tax_event)
    return new_tax_events


def rounding_report(tax_events, threshold, report_filename):
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"Decimaler stöds ej för bilaga K4 på skatteverket.se.\n")
        f.write(f"Här är en lista på avrundningar där det avrundade antalet skiljer sig mer än {str(threshold*100)[:4]}% från det egentliga antalet:\n")
        f.write(f"\n")
        for tax_event in tax_events:
            original = tax_event.amount
            rounded = round(tax_event.amount)
            if abs(rounded - original) / original > threshold:
                f.write(f"{original} {tax_event.name} har avrundats till {rounded} {tax_event.name}\n")

    if os.stat(report_filename).st_size > 999:
        raise Exception("Rounding report is longer than 999 characters (the limit on skatteverket.se), consider increasing the threshold --rounding-report-threshold and doing a simplified K4 --simplified-k4.")


def convert_to_integer_amounts(tax_events):
    new_events = []
    for tax_event in tax_events:
        tax_event.amount = round(tax_event.amount)
        new_events.append(tax_event)
    return new_events


def convert_to_integer_amounts_with_prefix(tax_events, precision_loss_tolerance=0.1):
    prefixes = [("", 1.0), ("milli", 1000.0), ("micro", 1000000.0)]

    # Check which coins need to be modified to not lose to much precision.
    coin_prefixes = {}
    coins = set([x.name for x in tax_events])
    for coin in coins:
        if not is_fiat(coin):
            for (prefix, factor) in prefixes:
                loss = max([abs(round(factor*x.amount) - factor*x.amount) / (factor*x.amount)
                            for x in tax_events if x.name == coin])
                if loss < precision_loss_tolerance:
                    break
            else:
                raise Exception("No prefix with low enough loss found")
            coin_prefixes[coin] = (prefix, factor)

    # Convert amount to integer
    new_events = []
    for tax_event in tax_events:
        if tax_event.name in coin_prefixes:
            tax_event.amount = round(coin_prefixes[tax_event.name][1] * tax_event.amount)
            tax_event.name = f"{coin_prefixes[tax_event.name][0]}{tax_event.name}"
        else:
            tax_event.amount = round(tax_event.amount)
        new_events.append(tax_event)

    return new_events


def convert_sek_to_integer_amounts(tax_events):
    new_events = []
    for tax_event in tax_events:
        tax_event.income = round(tax_event.income)
        tax_event.cost = round(tax_event.cost)
        new_events.append(tax_event)
    return new_events


def generate_k4_pages(year, personal_details, tax_events, stock_tax_events=None):
    def generate_section(events):
        lines = []
        num_sums = [0, 0, 0, 0]
        for event in events:
            k4_fields = event.k4_fields()
            line = []
            for (field_index, field) in enumerate(k4_fields):
                if field_index > 3:
                    line.append(str(field) if field else None)
                else:
                    line.append(str(field) if field else "0")
                if field_index > 1 and field:
                    num_sums[field_index-2] += field
            lines.append(line)
        sums = [str(sum) if sum > 0 else None for sum in num_sums]
        return K4Section(lines, sums)

    fiat_events = [x for x in tax_events if is_fiat(x.name)]
    crypto_events = [x for x in tax_events if not is_fiat(x.name)]

    pages = []
    page_number = 1
    while True:
        if stock_tax_events:
            section_a_events = stock_tax_events[(page_number-1)*9:page_number*9]
        else:
            section_a_events = []
        section_c_events = fiat_events[(page_number-1)*7:page_number*7]
        section_d_events = crypto_events[(page_number-1)*7:page_number*7]
        if not section_a_events and not section_c_events and not section_d_events:
            break
        section_a = generate_section(section_a_events)
        section_c = generate_section(section_c_events)
        section_d = generate_section(section_d_events)
        pages.append(K4Page(year, personal_details, page_number,
                            section_a, section_c, section_d))
        page_number += 1
    return pages


def generate_k4_sru(pages, personal_details, destination_folder):
    # Generate info.sru
    lines = []
    lines.append("#DATABESKRIVNING_START")
    lines.append("#PRODUKT SRU")
    lines.append("#FILNAMN BLANKETTER.SRU")
    lines.append("#DATABESKRIVNING_SLUT")
    lines.append("#MEDIELEV_START")
    lines.append(f"#ORGNR {personal_details.personnummer}")
    lines.append(f"#NAMN {personal_details.namn}")
    lines.append(f"#POSTNR {personal_details.postnummer}")
    lines.append(f"#POSTORT {personal_details.postort}")
    lines.append("#MEDIELEV_SLUT")
    lines.append("")

    with open(os.path.join(destination_folder, "info.sru"), "w", encoding="iso-8859-1") as f:
        f.write("\n".join(lines))

    # Generate blanketter.sru
    lines = []
    for page in pages:
        lines.extend(page.generate_sru_lines())
    lines.append("#FIL_SLUT")
    lines.append("")
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    with open(os.path.join(destination_folder, "blanketter.sru"), "w", encoding="iso-8859-1") as f:
        f.write("\n".join(lines))


def generate_k4_pdf(pages, destination_folder):
    for page in pages:
        page.generate_pdf(destination_folder)


def generate_calculation_report(trade_events):

    def write_csv(f, trade_events):
        f.write("Datum\tSymbol\tTyp\tHändelse\tAntal\tPris\tTotalt antal\tTotalt omkostnadsbelopp\tGenomsnittligt omkostnadsbelopp\tVinst\tFörlust\n")
        for t in trade_events:
            if t.amount > 0:
                f.write(f"{t.date}\t{t.name}\t{t.trade_type}\tKöp\t{t.amount}\t{t.price}\t{t.total_amount_after}\t{t.cost_basis_after*t.total_amount_after}\t{t.cost_basis_after}\t\t\n")
            if t.amount < 0:
                profit = t.tax_event.profit() if t.tax_event.profit() > 0 else ''
                loss = -t.tax_event.profit() if t.tax_event.profit() < 0 else ''
                f.write(f"{t.date}\t{t.name}\t{t.trade_type}\tSälj\t{t.amount}\t{t.price}\t{t.total_amount_after}\t{t.cost_basis_after*t.total_amount_after}\t{t.cost_basis_after}\t{profit}\t{loss}\n")

    # Write report
    with open(f"out/calculcation_report.csv", "w") as f:
        write_csv(f, trade_events)

    # Write individual reports per coin
    symbols = list(set([t.name for t in trade_events]))
    symbols.sort()
    for symbol in symbols:
        with open(f"out/calculcation_report_{symbol}.csv", "w") as f:
            write_csv(f, [t for t in trade_events if t.name == symbol])

def output_totals(tax_events, stock_tax_events = None):
    crypto_tax_events = [x for x in tax_events if not is_fiat(x.name)]
    fiat_tax_events = [x for x in tax_events if is_fiat(x.name)]

    if stock_tax_events:
        stock_total_profit = sum([x.profit() if x.profit() > 0 else 0 for x in stock_tax_events])
        stock_total_loss = sum([-x.profit() if x.profit() < 0 else 0 for x in stock_tax_events])
        print("Section A")
        print(f"  Summed profit (box 7.4): {stock_total_profit}")
        print(f"  Summed loss (box 8.3): {stock_total_loss}")
    fiat_total_profit = sum([x.profit() if x.profit() > 0 else 0 for x in fiat_tax_events])
    fiat_total_loss = sum([-x.profit() if x.profit() < 0 else 0 for x in fiat_tax_events])
    print("Section C")
    print(f"  Summed profit (box 7.2): {fiat_total_profit}")
    print(f"  Summed loss (box 8.1): {fiat_total_loss}")
    crypto_total_profit = sum([x.profit() if x.profit() > 0 else 0 for x in crypto_tax_events])
    crypto_total_loss = sum([-x.profit() if x.profit() < 0 else 0 for x in crypto_tax_events])
    print("Section D")
    print(f"  Summed profit (box 7.5): {crypto_total_profit}")
    print(f"  Summed loss (box 8.4): {crypto_total_loss}")
    print(f"  Section D Tax: {round(0.3*(crypto_total_profit - 0.7*crypto_total_loss))}")
