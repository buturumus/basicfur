from django import forms

class myForm(forms.Form):
    input_name = forms.CharField(max_length = 50)
    