# Swedish cryptocurrency tax reporting script

## About

This is a tool to convert your cryptocurrency trade history to the K4 documents needed
for tax reporting to Skatteverket.

Using [cointracking.info](https://cointracking.info?ref=D611015) is currently the
only supported way to import trades. This site does not yet support doing tax
reports using average cost basis which is what is required in Sweden but
it is still very useful for the actual trade data import.

Besides adding support for average cost basis this script can also generate files
which are compatible with Skatteverket. There is either PDF output for printing and
sending by mail or SRU-output which can be imported on skatteverket.se.

## Supporting the development

Please consider supporting the development of this tool by either using
the referral link to [cointracking.info](https://cointracking.info?ref=D611015)
or by donating to one of the adresses below. Using the referral link
will give you a 10% discount if you decide to buy a Pro or Unlimited account.

* BTC: `3KTLVpWjRGuJNBmjsKo4HGDG1G5SCesej3`
* ETH: `0x05125B8E6598AbDDe21c7D01008a10F6107Ce004`

## How coins should be entered on [cointracking.info](https://cointracking.info?ref=D611015)

* Trade: Trades fiat->crypto, crypto->crypto and crypto->fiat.
* Mining (only income): Gets a cost basis of the value at the time the crypto
was received. The actual income should be declared manually on a
[T2 form "Inkomst av tjänst för inkomstgivande hobby"](https://www.skatteverket.se/privat/sjalvservice/blanketterbroschyrer/blanketter/info/2051.4.39f16f103821c58f680006232.html).
* Gift/Tip (only income): Used for reporting hard forks and airdrops, these
cryptos will get a cost basis of 0.
* Spend: Used when paying with crypto, treated as a sell of the currency in question.

A common mistake is to forget to report the conversion to/from Euro which
the bank does when transfering to an exchange such as Kraken/Bitstamp. There
should be a trade between SEK and EUR on cointracking to make sure that there
are EUR available when later exchanging it to crypto.

Withdrawals/Deposits are ignored for the tax report as these are assumed to be
transfers of funds between wallets owned by you.

If you have other types of income in crypto this isn't
handled by the script yet.

Adding new rules for handling more situations shouln't be that hard as long as
it is easy to define the cost basis for an income and what the price should be
when selling crypto. You can add feature requests and if it isn't to complicated
I'll try to add it to the script, or you can submit a pull request.

## Limitations

The sru format is currently limited in that it doesn't allow
decimals, this is a limitation with skatteverket.se. The
recommendation from Skatteverket is to round to whole numbers
even if that results in 0 BTC or similar being reported and then
report what roundings have been done under Övriga Upplysningar.

The script can now generate a rounding report which can be
pasted in Övriga Upplysningar. Skatteverket limits the size of
this field to 999 characters so it is best to combine this with
doing a simplified K4 report to reduce the number of lines which
has to be reported in the K4.

## Liability

I'm not taking any responsibility for that this tool will generate a
correct tax report. I am using the tool for my own tax reporting though
so making it correct is a priority to me. You will however have to
take responsibility yourself for the tax report you send to
Skatteverket, this means you should perform a sanity check of some sort
on the generated K4 documents to make sure it looks reasonable.

## Setup

### Windows

There is a packaged version for Windows under releases which can be used.
Change the example command lines below from `python report.py` to
`report.exe` instead if using it.

### macOS

There is a packaged version for macOS under releases which can be used.
Change the example command lines below from `python report.py` to
`./report` instead if using it.

### Other (or if you prefer setting up python yourself)

Python 3.6 is required.

The following python packages are needed for pdf generation.

* pdfrw
* reportlab

Python virtualenv can be setup using

```
virtualenv venv -p python3.6
. ./venv/bin/activate
pip install -r requirements.txt
```

## Input data

### data/personal_details.json

This file should have the following format. Make sure to save the file in UTF-8 format. On Windows you can install Notepad++ to make this easier.

```
{
	"namn": "Full name",
	"personnummer": "YYYYMMDD-NNNN",
	"postnummer": "NNNNN",
	"postort": "City"
}
```

### data/trades.csv

To get the data for this file you first need to have your complete trade history
on [cointracking.info](https://cointracking.info?ref=D611015). Then go to the
Trade Prices-page and download a CSV report from that page and store it at
`data/trades.csv`.

### data/stocks.json (optional)

If you have any stock trades which need to be reported in section A on the K4 then you can
enter them in `data/stocks.json`. See `data/stocks_template.json` for the format.

## Running

### Options

```
usage: report.py [-h] [--trades TRADES] [--out OUT] [--format {pdf,sru}]
                 [--decimal-sru]
                 [--exclude-groups [EXCLUDE_GROUPS [EXCLUDE_GROUPS ...]]]
                 [--coin-report] [--simplified-k4] [--rounding-report]
                 [--rounding-report-threshold ROUNDING_REPORT_THRESHOLD]
                 year

Swedish cryptocurrency tax reporting script

positional arguments:
  year                  Tax year to create report for

optional arguments:
  -h, --help            show this help message and exit
  --trades TRADES       Read trades from csv file
  --out OUT             Output folder
  --format {pdf,sru}    The file format of the generated report
  --decimal-sru         Report decimal amounts in sru mode (not supported by
                        Skatteverket yet)
  --exclude-groups [EXCLUDE_GROUPS [EXCLUDE_GROUPS ...]]
                        Exclude cointracking group from report
  --coin-report         Generate report of remaining coins and their cost
                        basis at end of year
  --simplified-k4       Generate simplified K4 with only two line per coin
                        type (aggregated profit and loss).
  --rounding-report     Generate report of roundings done which can be pasted
                        in Ovriga Upplysningar, the file will be put in the
                        out folder.
  --rounding-report-threshold ROUNDING_REPORT_THRESHOLD
                        The number of percent difference required for an
                        amount to be included in the report.
```

### Example

#### Generate a simplified report for 2017 in sru format.

```
python report.py 2017 --simplified-k4
```

Generated sru files can be found in the ```out``` folder.

Generated sru files can be tested for errors at [https://www.skatteverket.se/filoverforing]

#### Generate a simplified report for 2017 in sru format with a rounding report with threshold of 1%.

```
python report.py 2017 --simplified-k4 --rounding-report --rounding-report-threshold=1
```

Generated sru files and the rounding report can be found in the ```out``` folder.

Generated sru files can be tested for errors at [https://www.skatteverket.se/filoverforing]

#### Generate report for 2017 in pdf format.

```
python report.py --format=pdf 2017
```

Generated pdf files can be found in the ```out``` folder.

#### Merging the generated pdf files

Merging the pdf files can be done with Ghostscript. It might make printing a bit easier.

```
cd out
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=merged.pdf k4_no*.pdf
```
