# timey-wimey

## Set up

(1) Enable the google calendar API by following step 1
at https://developers.google.com/calendar/quickstart/python 

(2) Copy credentials.json to this directory

(3) Install pip packages:

```
$ pip install -r requirements.txt
```

## Running

```
$ python main.py
```

Voila! By default, it computes time spent in all your displayed calendars in google calendar. To override this, you can
pass in a list of strings, e.g.

```
$ python main.py --calendar_names="Reading and stuff","Derping around"
```
