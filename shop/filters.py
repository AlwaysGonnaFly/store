from django.db.models import Q
from django.forms import HiddenInput, TextInput

from .models import Good, Subcategory, Category, GoodInfo1, GoodInfo2

import django_filters


class GoodFilter(django_filters.FilterSet):
    ORDERING = {'price': 'Дешёвые', '-price': 'Дорогие', 'time': 'Старые', '-time': 'Новые'}

    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), widget=HiddenInput())
    subcategory = django_filters.ModelChoiceFilter(queryset=Subcategory.objects.all(), widget=HiddenInput())
    o = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('id', 'time'),
        ),
        field_labels=ORDERING,
    )
    q = django_filters.CharFilter(method='search_filter', widget=TextInput(attrs={
        'placeholder': 'Запрос',
        'class': 'form-control',
    }))
    p4 = django_filters.CharFilter(method='info1_filter', widget=HiddenInput())
    p3 = django_filters.CharFilter(method='info2_filter', widget=HiddenInput())

    def info1_filter(self, queryset, name, value):
        if value:
            ids = map(str, GoodInfo1.objects.values_list('id', flat=True))
            for i in value.split('%'):
                if i in ids:
                    queryset = queryset.filter(param4__id=i)
        return queryset

    def info2_filter(self, queryset, name, value):
        if value:
            ids = map(str, GoodInfo2.objects.values_list('id', flat=True))
            for i in value.split('%'):
                if i in ids:
                    queryset = queryset.filter(param3__id=i)
        return queryset

    def search_filter(self, queryset, name, value):
        if value:
            return queryset.filter(Q(name__iregex=value))
        return queryset

    class Meta:
        model = Good
        fields = ['category', 'subcategory']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields['o'].widget.attrs = {
            'style': 'display: none;'
        }
