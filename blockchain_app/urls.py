from django.urls import path
from . import views

app_name = 'ledger_app'

urlpatterns = [
    path('', views.ledger_view, name='ledger'),
    # path('add_block/', views.add_block, name='add_block'),  <-- remove this
]
