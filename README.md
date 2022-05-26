
--------------------------------------------------------------
BasicFur - Basic accounting and store for Furniture production
--------------------------------------------------------------

It is a modern clone of some old and buggy ms access app which is still used by a few small- and middle-sized manufacturing companies in Ukraine. 
Mainly these guys are furniture makers but the application is very common and does not have any furniture-specific features. 



=== What's it all about ===

This is a web application which allows you to enter, save and analyse information about money transfers, purchases, inventories, stock etc for a small production company. It uses classical accounting principles such as money/goods movements, double entries, account charts and so on.

Initially there was limited set of features in the old prototype software and the main goal was to reproduce them only. There is custom chart of accounts and limited set of transactions (with maybe unusual names if you are an accountant). It planned to be runned on a couple of PCs with Firefox and some dedicated server, so the app is NOT mobile-adapted and nobody payed great attention to performance.



=== Accounting concept ===

First, there are lists of partners and materials (goods and services) in app, and tools to add/edit/remove them.
Then, there are typical transactions which used in company's activity: purchase of materials, transfer money, transfer materials from inventories to production, registration of produced goods at stock, shipping. Also there are transactions for worker's salaries, petty cash operations etc. All results and current state of things are visible in different analytical tables.

Every operation can be called from collapsible sidebar menu.
Also there's set of filters in the sidebar, which can be applied to analytical tables, with elements of search.  

Every transaction belongs to one of two groups: money movements and goods movements. Latter contains specification, i.e.extra set of fields related to some goods, their price (or 2 prices: purchase and selling) and quantity. 
Apart from maybe unusual names there are some other features which had to be cloned 'as is' from the prototype software. For example, negative balance is some tables should be shown simply with '-' sign but in other place with 'D' or 'C' prefix (Debit/Credit). 



=== Development stack ===

This project is a pet project!

Backend is written in Django and PostgreSQL.
Frontend - in Bootstrap + JavaScript, with active usage of JQuery + AJAX.

Django.
Models are as simple as possible.
Views are class-based though not in classical meaning of the term. Initial goal was to try to create them from scratch so majority of view classes are not generic but custom.  

Frontend.
It uses Bootstrap and small set of custom JS scripts. As it was said before the app was planned to be used in Firefox and it looks ok there. In Chrome at the moment the project doesn't look correct because of well-known problem with width of Bootstrap-based tables.
All input fields, control buttons and data tables located in the tabs of main page, and the tabs change dynamically with AJAX calls. 



=== Live preview ===

Currently the project can be viewed on Heroku:


https://safe-citadel-44106.herokuapp.com/


username: test
password: test



=== Some screenshots ===

![Animated GIF 01...](/screenshots/01.gif?raw=true)

![Animated GIF 02...](/screenshots/02.gif?raw=true)

![Animated GIF 03...](/screenshots/03.gif?raw=true)



=== Contacts ===


e-mail:   buturumus@gmail.com


telegram: @buturumus


Alexander



