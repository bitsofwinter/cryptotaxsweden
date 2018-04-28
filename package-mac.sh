builddir=/tmp/build_cts
repo=$builddir/repo
distbase=$builddir/dist
distdir=cryptotaxsweden
package=$distdir.zip

virtualenv $builddir/tempenv
. $builddir/tempenv/bin/activate
deactivate

rm -rf $builddir
mkdir -p $builddir
git clone . $repo
cd $repo
virtualenv -p python3.6 venv
. venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile report.py
mkdir -p $distbase/$distdir
cp dist/report $distbase/$distdir/
cp README.md $distbase/$distdir/
cp LICENSE $distbase/$distdir/
mkdir $distbase/$distdir/data
cp data/personal_details_template.json $distbase/$distdir/data/
cp data/stocks_template.json $distbase/$distdir/data/
mkdir $distbase/$distdir/docs
cp docs/K4.pdf $distbase/$distdir/docs/
cd $distbase
zip -r $package $distdir
