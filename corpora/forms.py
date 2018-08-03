from django import forms

class CorpusForm(forms.Form):
    """
    For editing a corpus (text document)

    Right now we only really want year to be editable.
    """
    year = forms.DateField(label="Year",
                            required=True,
                            widget=forms.DateInput(attrs={'class': 'form-control'}))

class ConcordanceForm(forms.Form):
    """
    Concordance query terms
    """
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
    """
    Query terms for analysis, that is, the resulting graph.
    """
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

    X = [("years", "years"), ("tags", "tags"), ("none", "none")]
    Y = [("count", "count"), ("percentage", "percentage"), ("distribution", "distribution")]
    x_axis = forms.CharField(label="X Axis",
                            required=True,
                            widget=forms.Select(choices=X, attrs={'class': 'form-control'})#, default="years")
    )
    y_axis = forms.CharField(label="Y Axis",
                            required=True,
                            widget=forms.Select(choices=Y, attrs={'class': 'form-control'})#, default="counts")
    )

class GraphForm(forms.Form):
    """
    File specification for the downloadable graph.
    """
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
