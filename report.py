#!/usr/bin/env python3
import argparse
import datetime
import os
import sys
from enum import Enum

from taxdata import PersonalDetails, Trades, TaxEvent
import tax


class Format(Enum):
    pdf = 'pdf'
    sru = 'sru'

    def __str__(self):
        return self.value

parser = argparse.ArgumentParser(description='Swedish cryptocurrency tax reporting script')
parser.add_argument('year', type=int,
                    help='Tax year to create report for')
parser.add_argument('--trades', help='Read trades from csv file', default='data/trades.csv')
parser.add_argument('--out', help='Output folder', default='out')
parser.add_argument('--format', type=Format, choices=list(Format), default=Format.sru,
                    help='The file format of the generated report')
parser.add_argument('--decimal-sru', help='Report decimal amounts in sru mode (not supported by Skatteverket yet)', action='store_true')
parser.add_argument('--exclude-groups', nargs='*', help='Exclude cointracking group from report')
parser.add_argument('--coin-report', help='Generate report of remaining coins and their cost basis at end of year', action='store_true')
parser.add_argument('--simplified-k4', help='Generate simplified K4 with only two line per coin type (aggregated profit and loss).', action='store_true')
parser.add_argument('--rounding-report', help='Generate report of roundings done which can be pasted in Ovriga Upplysningar, the file will be put in the out folder.', action='store_true')
parser.add_argument('--rounding-report-threshold', help='The number of percent difference required for an amount to be included in the report.', default='1')
parser.add_argument('--cointracking-usd', help='Use this flag if you have configured cointracking calculate prices in USD. Conversion from USD to SEK will then be done by this script instead.', action='store_true')
parser.add_argument('--max-overdraft', type=float, help='The maximum overdraft to allow for each coin, at the event of an overdraft the coin balance will be set to zero.', default=1e-9)
opts = parser.parse_args()

if not os.path.isdir(opts.out):
    os.makedirs(opts.out)

personal_details = PersonalDetails.read_from("data/personal_details.json")
trades = Trades.read_from(opts.trades, opts.cointracking_usd)
stock_tax_events = TaxEvent.read_stock_tax_events_from("data/stocks.json") if os.path.exists("data/stocks.json") else None

tax_events = tax.compute_tax(trades,
                             datetime.datetime(year=opts.year,month=1,day=1,hour=0, minute=0),
                             datetime.datetime(year=opts.year,month=12,day=31,hour=23, minute=59),
                             opts.max_overdraft,
                             exclude_groups=opts.exclude_groups if opts.exclude_groups else [],
                             coin_report_filename=os.path.join(opts.out, "coin_report.csv") if opts.coin_report else None
                             )
if tax_events is None:
    print(f"Aborting tax computation.")
    sys.exit(1)

if opts.simplified_k4:
    tax_events = tax.aggregate_per_coin(tax_events)

if opts.format == Format.sru and not opts.decimal_sru:
    if opts.rounding_report:
        threshold = float(opts.rounding_report_threshold) / 100.0
        tax.rounding_report(tax_events, threshold, os.path.join(opts.out, "rounding_report.txt"))
    tax_events = tax.convert_to_integer_amounts(tax_events)

tax_events = tax.convert_sek_to_integer_amounts(tax_events)

pages = tax.generate_k4_pages(opts.year, personal_details, tax_events, stock_tax_events=stock_tax_events)

if opts.format == Format.sru:
    tax.generate_k4_sru(pages, personal_details, opts.out)
elif opts.format == Format.pdf:
    tax.generate_k4_pdf(pages, opts.out)

tax.output_totals(tax_events, stock_tax_events=stock_tax_events)
