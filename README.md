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
sending by mail or SRU-output which can be imported on skatteverket.se if the number
of sales does not exceed 300.

## Supporting the development

Please consider supporting the development of this tool by either using
the referral link to [cointracking.info](https://cointracking.info?ref=D611015)
or by donating to one of the adresses below. Using the referral link
will give you a 10% discount if you decide to buy a Pro or Unlimited account.

* BTC: `3KTLVpWjRGuJNBmjsKo4HGDG1G5SCesej3`
* ETH: `0x05125B8E6598AbDDe21c7D01008a10F6107Ce004`
* LTC: `MTwzCUPayUSiatC6g2Y8JPMd9myTjKbjEJ`

## Input data

For importing trade history from exchanges etc an account at
[cointracking.info](https://cointracking.info?ref=D611015) is required.
Once all trading history has been imported there you can use the
Trade Prices-page to get the required data for this script.

## Limitations

The sru format is currently limited in that it doesn't allow
decimals, the script solves this by reporting milli/micro amounts for the
currencies where the traded amount is very small.

For example if 0.025 BTC was sold it will convert this to 25 milliBTC. It
remains to check with Skatteverket how they prefer to get this reported.

It could be that pdf reports will be preferable in this case.

## Liability

I'm not taking any responsibility for that this tool will generate a
correct tax report. I am using the tool for my own tax reporting though
so making it correct is a priority to me. You will however have to
take responsibility yourself for the tax report you send to
Skatteverket, this means you should perform a sanity check of some sort
on the generated K4 documents to make sure it looks reasonable.

## Setup

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

This file should have the following format.

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
Trade Prices-page and press the "Copy Table" button and then paste into
`data/trades.csv`

### data/stocks.json (optional)

If you have any stock trades which need to be reported in section A on the K4 then you can
enter them in `data/stocks.json`. See `data/stocks_template.json` for the format.

## Running

### Options

```
usage: report.py [-h] [--format {pdf,sru}] [--decimal-sru] year

Swedish cryptocurrency tax reporting script

positional arguments:
  year                Tax year to create report for

optional arguments:
  -h, --help          show this help message and exit
  --format {pdf,sru}  The file format of the generated report
  --decimal-sru       Report decimal amounts in sru mode (not supported by
                      Skatteverket yet)
```

### Example

#### Generate report for 2017 in pdf format.

```
python report.py <year>
```

Generated pdf files can be found in the ```out``` folder.

#### Generate report for 2017 in sru format.

```
python report.py --format=sru <year>
```

Generated sru files can be found in the ```out``` folder.

Generated sru files can be tested for errors at [https://www.skatteverket.se/filoverforing]
