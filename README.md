# cyp-scan
Web crawler for scanning Cyprus job boards (Twisted)

Installation
------------
`virtualenv env`

`pip install -r requirements.txt`

Start search
------------
Basic usage: `python cyp.py javascript python`

Results saved to default Excel file `jobs.xlsx` 


Options
-------
You can specify output xls-file with `-o` attribute:
`python cyp.py python twisted -o result.xlsx`

Also you can set how many pages to parse with `-p` and `-m` keys combination:

`python cyp.py manager analyst -p 20 -m 600`  -- find "manager or analyst" jobs 
scanning 20 rows per page and 600 rows total
 
