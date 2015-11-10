from django.shortcuts import render, redirect
from django.views.generic import View
from parseraux import *
from datetime import date, datetime, time, timedelta
from django.http import HttpResponse
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

# Create your views here.
class Index(View):
    template_name = 'nexreporter/index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        f = request.FILES['CSV'].read()
        start = datetime.strptime(request.POST['intervalo_inicio'], '%m/%d/%Y %I:%M %p')
        end = datetime.strptime(request.POST['intervalo_fin'], '%m/%d/%Y %I:%M %p')
        extra = int(request.POST['extra'])
        extra_info = []
        client = request.POST['client']
        extra_info.append([request.POST['client'],request.POST['invoice']])
        interval = start.strftime('%d ')\
        + get_month_name(start.month) + start.strftime(' %y')\
        + ' - ' + (end-timedelta(days=1)).strftime('%d ')\
        + get_month_name(end.month) + end.strftime(' %y')

        for x in xrange(0, extra):
            name = request.POST['nombre_'+str(x)]
            total = request.POST['total_'+str(x)]
            cant = request.POST['cantidad_'+str(x)]
            extra_info.append([name,total,cant])

        output = StringIO.StringIO()

        make_cut(parse(f),output, start, end, extra_info)
        output.seek(0)

        response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename="+interval+" "+client+".xlsx"

        return response

class Listo(View):
    template_name = 'nexreporter/listo.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)