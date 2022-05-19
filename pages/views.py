# views.py 

import re, time, datetime, decimal
from decimal import Decimal

from django.shortcuts import render 

from django.apps import AppConfig
from django.apps import apps

from django.db.models import Q, Sum

from django.db.models import Window, F
from django.db.models.functions import Lead

from django.views.generic import ListView
from django.views.generic import TemplateView 

from django.http import JsonResponse, Http404, HttpResponse
from django.template.loader import render_to_string

from .models import *

# some globals

# for debug
import logging

TABS_TEMPLATES_DIR = 'mainpage/tabs'
HEADER_TEMPLATE_FILENAME = 'header.html'

# cross-visible view parts
from .mainpage  import *
from .new_classes import *

####



