QCReport ( SMSMaama Reporting)
====================================================
QCReport is used for generating weekly reports on SMSMaama Rapidpro Project.


## Usage
```
#Clone the project
git clone https://github.com/faithNassiwa/qcreports.git

#Run migrations
python manage.py migrate

#Run command to update the database with project content( this might take awhile)
python manage.py smsmaama

#Run server
python manage.py runserver

#Check out url below in your browser to view the pdf report
http://127.0.0.1:8000/sms_maama_weekly_pdf
```


## Testing
`python manage.py test`


