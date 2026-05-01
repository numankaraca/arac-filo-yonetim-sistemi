import psycopg2
try:
    psycopg2.connect(dbname='arac_filo', user='postgres', password='password', host='localhost')
except Exception as e:
    print('ERROR_MSG:', e)
