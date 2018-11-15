from django import forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as t
from django.views import generic

from . import models


class ProcessTemplateNameViewMixin:
    node_name = None

    def get_template_names(self):
        names = [
            "%s/%s_%s.html" % (
                self.model._meta.app_label,
                self.model._meta.model_name,
                self.node_name,
            )
        ]
        names.extend(super().get_template_names())
        names.append("%s/process%s.html" % (
            self.model._meta.app_label,
            self.template_name_suffix
        ))
        return names


class TaskViewMixin(ProcessTemplateNameViewMixin):
    node_name = None

    def __init__(self, **kwargs):
        self._instance_kwargs = kwargs
        super().__init__(**kwargs)

    def get_task(self):
        try:
            return get_object_or_404(
                models.Task,
                pk=self.kwargs['pk'],
                node_name=self.node_name,
                completed=None,
            )
        except KeyError:
            return models.Task(
                node_name=self.node_name,
            )

    def get_object(self, queryset=None):
        task = self.get_task()
        return task.process

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        task = self.get_task()
        task.process = self.object
        task.finish()
        task.start_next_tasks()
        return response


class ProcessDetailView(ProcessTemplateNameViewMixin, generic.DetailView):
    pass


class ManualOverrideView(PermissionRequiredMixin, ProcessTemplateNameViewMixin, generic.UpdateView):
    permission_required = 'override'
    node_name = 'manual_override'
    fields = '__all__'

    @staticmethod
    def get_task_choices(process):
        for node_name in dict(process.get_nodes()).keys():
            yield node_name, node_name

    def get_form_class(self):
        form_class = super().get_form_class()

        class OverrideForm(form_class):
            next_tasks = forms.MultipleChoiceField(
                label=t('Next tasks'),
                choices=self.get_task_choices(self.object),
            )

        return OverrideForm

    def get_next_task_nodes(self, form):
        node_names = form.cleaned_data['next_tasks']
        for name in node_names:
            yield self.object.get_node(name)

    @transaction.atomic()
    def form_valid(self, form):
        next_nodes = self.get_next_task_nodes(form)
        response = super().form_valid(form)
        active_tasks = list(self.object.task_set.filter(completed=None))
        for task in active_tasks:
            task.finish()
        override_task = self.object.task_set.create(
            node_name='manual_override',
        )
        override_task.parent_task_set.set(active_tasks)
        override_task.finish()
        override_task.start_next_tasks(next_nodes=next_nodes)
        return response