from django import forms

class CorpusForm(forms.Form):
    year = forms.DateField(label="Year",
                            required=True,
                            widget=forms.DateInput(attrs={'class': 'form-control'}))

class ConcordanceForm(forms.Form):
    query = forms.CharField(label="Query",
                            required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    max_examples = forms.IntegerField(label="Max Examples",
                                      required=True,
                                      widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    srl = forms.MultipleChoiceField(choices=[("agent", "agent"),\
                                             ("patient", "patient"),\
                                             ("theme", "theme")],\
                                    widget=forms.CheckboxSelectMultiple(),
                                    required=False)

class AnalysisForm(forms.Form):
    query = forms.CharField(label="Query",
                            required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    srl = forms.MultipleChoiceField(choices=[("agent", "agent"),\
                                             ("patient", "patient"),\
                                             ("theme", "theme")],\
                                    widget=forms.CheckboxSelectMultiple(),
                                    required=False
    )
    years = forms.CharField(label="Years",
                            required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class GraphForm(forms.Form):
    name = forms.CharField(label="Name",
                            required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    file_type = forms.CharField(required=True,\
                                widget=forms.Select(choices=[("PDF", "pdf"),
                                                             ("PNG", "png")
                                                            ],
                                                    attrs={'class': 'form-control'})
                                )
