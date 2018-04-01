import argparse
import datetime
import os
from enum import Enum

from taxdata import PersonalDetails, Fees, Trades, TaxEvent
import tax


class Format(Enum):
    pdf = 'pdf'
    sru = 'sru'

    def __str__(self):
        return self.value


parser = argparse.ArgumentParser(description='Swedish cryptocurrency tax reporting script')
parser.add_argument('year', type=int,
                    help='Tax year to create report for')
parser.add_argument('--format', type=Format, choices=list(Format), default=Format.pdf,
                    help='The file format of the generated report')
parser.add_argument('--decimal-sru', help='Report decimal amounts in sru mode (not supported by Skatteverket yet)', action='store_true')
opts = parser.parse_args()


personal_details = PersonalDetails.read_from("data/personal_details.json")
trades = Trades.read_from("data/trades.csv")
stock_tax_events = TaxEvent.read_stock_tax_events_from("data/stocks.json") if os.path.exists("data/stocks.json") else None

tax_events = tax.compute_tax(trades,
                             datetime.datetime(year=opts.year,month=1,day=1,hour=0, minute=0),
                             datetime.datetime(year=opts.year,month=12,day=31,hour=23, minute=59),
                             exclude_groups=['Mining']
                             )

if opts.format == Format.sru and not opts.decimal_sru:
    tax_events = tax.convert_to_integer_amounts(tax_events)

pages = tax.generate_k4_pages(opts.year, personal_details, tax_events, stock_tax_events=stock_tax_events)

if opts.format == Format.sru:
    tax.generate_k4_sru(pages, personal_details, "out")
elif opts.format == Format.pdf:
    tax.generate_k4_pdf(pages, "out")

tax.output_totals(tax_events, stock_tax_events=stock_tax_events)
