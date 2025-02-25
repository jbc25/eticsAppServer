# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django_filters.views import FilterView

import helpers
from currency.models import Entity
from currency.views import EntityFilter
from helpers import superuser_required
from helpers.mixins.AjaxTemplateResponseMixin import AjaxTemplateResponseMixin
from helpers.mixins.ListItemUrlMixin import ListItemUrlMixin
from wallets.forms.PaymentForm import PaymentForm
from wallets.models import Payment, Wallet


@login_required
def pending_payments(request):
    pending_payments = Payment.objects.pending(user=request.user)
    sent_pending = Payment.objects.sent_pending(user=request.user)

    page = request.GET.get('page')
    pending_payments = helpers.paginate(pending_payments, page, elems_perpage=10)

    params = {
        'payments': pending_payments,
        'sent_pending': sent_pending
    }

    if request.is_ajax():
        response = render(request, 'payment/query.html', params)
        response['Cache-Control'] = 'no-cache'
        response['Vary'] = 'Accept'
        return response
    else:
        return render(request, 'payment/pending_payments.html', params)



@login_required
def payment_detail(request, pk):

    payment = get_object_or_404(Payment, pk=pk)
    can_edit = request.user == payment.receiver or request.user.is_superuser
    can_view = request.user == payment.sender or request.user.is_superuser

    if not can_edit and not can_view:
        messages.add_message(request, messages.ERROR, 'No tienes permisos para ver este pago')
        return redirect('pending_payments')


    params = { 'payment': payment, 'can_edit':can_edit }

    if request.method == "POST" and can_edit:
        action = request.POST.get("action", "")
        if action == 'accept':
            try:
                payment.accept_payment()
                if request.is_ajax():
                    return JsonResponse({'success':True})
                else:
                    messages.add_message(request, messages.SUCCESS, 'Pago aceptado con éxito')
                    if request.user.is_superuser:
                        return redirect('admin_payments')
                    else:
                        return redirect('pending_payments')
            except Wallet.NotEnoughBalance:
                params['notenoughbalance'] = True
                if request.is_ajax():
                    response = JsonResponse({'error':'notenoughbalance', 'error_message':'El monedero no tiene saldo suficiente.'})
                    response.status_code = 400
                    return response

        if action == 'cancel':
            payment.cancel_payment()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.add_message(request, messages.SUCCESS, 'Pago rechazado con éxito')
                if request.user.is_superuser:
                    return redirect('admin_payments')
                else:
                    return redirect('pending_payments')

    sender_type, sender = payment.sender.get_related_entity()
    receiver_type, entity = payment.receiver.get_related_entity()
    params['sender'] = sender
    params['receiver'] = entity

    if receiver_type == 'entity':
        params['bonus'] = entity.bonus(payment.total_amount, sender_type)

    return render(request, 'payment/detail.html', params)


class SelectPaymentReceiverView(FilterView, ListItemUrlMixin, AjaxTemplateResponseMixin):

    model = Entity
    queryset = Entity.objects.active()
    objects_url_name = 'create_payment'
    template_name = 'payment/select_entity.html'
    ajax_template_name = 'payment/entity.html'
    filterset_class = EntityFilter
    paginate_by = 9

    def get_context_data(self, **kwargs):
        context = super(SelectPaymentReceiverView, self).get_context_data(**kwargs)
        UserModel = get_user_model()
        type, instance = UserModel.get_related_entity(self.request.user)
        context['is_entity'] = type == 'entity'

        return context


@login_required
def new_payment(request, pk):

    entity = get_object_or_404(Entity, pk=pk)
    UserModel = get_user_model()
    type, instance = UserModel.get_related_entity(request.user)
    data = {
        'receiver': entity,
        'is_sender_entity': type == 'entity',
    }

    if request.method == "POST":
        form = PaymentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                payment = form.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Pago enviado con éxito')
                return redirect('payment_detail', pk=payment.pk)
            except Wallet.WrongPinCode:
                print 'Wrong pincode!'
                data['wrongpingcode'] = True
            except Wallet.NotEnoughBalance:
                data['notenoughbalance'] = True
        else:
            print form.errors.as_data()
    else:
        form = PaymentForm(initial={'sender':request.user, 'receiver':entity.user})

    data['form'] = form
    return render(request, 'payment/create.html', data)


@superuser_required
def admin_payments(request):
    payments = Payment.objects.all().order_by('-timestamp')

    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)

    email = request.GET.get('email')
    if email:
        payments = payments.filter(sender__email=email) | payments.filter(receiver__email=email)

    page = request.GET.get('page')
    payments = helpers.paginate(payments, page, elems_perpage=10)
    params = {
        'payments': payments,
        'showing_all': True
    }

    if request.is_ajax():
        response = render(request, 'payment/query.html', params)
        response['Cache-Control'] = 'no-cache'
        response['Vary'] = 'Accept'
        return response
    else:
        return render(request, 'payment/admin.html', params)