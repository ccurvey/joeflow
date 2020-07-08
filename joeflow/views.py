from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404
from django.views import generic

from . import forms, models
from .contrib.reversion import RevisionMixin


class ProcessTemplateNameViewMixin:
    name = None

    def get_template_names(self):
        names = [
            "%s/%s_%s.html"
            % (self.model._meta.app_label, self.model._meta.model_name, self.name,)
        ]
        names.extend(super().get_template_names())
        names.append(
            "%s/process%s.html"
            % (self.model._meta.app_label, self.template_name_suffix)
        )
        return names


class TaskViewMixin(ProcessTemplateNameViewMixin, RevisionMixin):
    name = None

    def __init__(self, **kwargs):
        self._instance_kwargs = kwargs
        super().__init__(**kwargs)

    def get_task(self):
        try:
            return get_object_or_404(
                models.Task, pk=self.kwargs["pk"], name=self.name, completed=None,
            )
        except KeyError:
            return models.Task(name=self.name, type=models.Task.HUMAN)

    def get_object(self, queryset=None):
        task = self.get_task()
        return task.process

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.create_task(request)
        return response

    def create_task(self, request):
        task = self.get_task()
        task.process = self.model._base_manager.get(pk=self.object.pk)
        task.finish(request.user)
        task.start_next_tasks()
        return task


class ProcessDetailView(ProcessTemplateNameViewMixin, generic.DetailView):
    pass


class OverrideView(
    PermissionRequiredMixin,
    RevisionMixin,
    ProcessTemplateNameViewMixin,
    generic.UpdateView,
):
    permission_required = "override"
    name = "override"
    form_class = forms.OverrideForm
    fields = "__all__"

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class, fields=self.fields)

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        form.start_next_tasks(self.request.user)
        return response
