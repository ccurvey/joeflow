.. _tutorial-templates:

Creating templates
==================

Your human tasks, like your `start` view will need a template. The template
name is similar as it is for a
:class:`CreateView<django.views.generic.edit.CreateView>` but with more
options. Default template names are::

    personnel/welcomeworkflow_start.html
    personnel/welcomeworkflow_form.html
    personnel/workflow_form.html

Django will search for a template precisely that order. This allows you to
create a base template for all human tasks but also override override them
individually should that be needed.

Following the example please create a new ``templates/personnel`` directory (inside your existing "personnel" directory, and
within there, create a file named ``welcomeworkflow_start.html``

Now fill the file with a simple form template:

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Welcome Workflow</title>
    </head>
    <body>
      <form method="POST">
        {% csrf_token %}
        {{ form }}
        <input type="submit">
      </form>
    </body>
    </html>

Of course you can make it prettier, but this will work.

Restart your development server, then hit http://localhost:8000/personnel/welcome/start/  
You should see a nice form.  But there are no users set up in our system yet,
set let's create a superuser called "alex".  (Usually this would not be a superuser,
but we need something to touch.)

.. code-block:: bash

    $ python manage.py createsuperuser 
    Username (leave blank to use 'xxxx'): alex
    Email address: alex@example.com
    Password: 
    Password (again): 
    This password is too short. It must contain at least 8 characters.
    This password is too common.
    Bypass password validation and create user anyway? [y/N]: y   
    Superuser created successfully.

Now we can go back to http://localhost:8000/personnel/welcome/start/ , and we
can see "alex" in the drop-down.  Choose Alex, hit "submit"....and you'll get
another "TemplateDoesNotExist" error.  That's OK...there's another template
we just have to create a template for the detail view.  

Create a ``templates/personnel/welcomeworkflow_detail.html`` page and put this in it:

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Welcome Workflow</title>
    </head>
    <body>
      {{ object.get_instance_graph_svg }}
      <h1>{{ object }}</h1>
      <table>
        <thead>
        <tr>
          <th>id</th>
          <th>task name</th>
          <th>completed</th>
        </tr>
        </thead>
        <tbody>
        {% for task in object.task_set.all %}
        <tr>
          <td>{{ task.pk }}</td>
          <td>
            {% if task.get_absolute_url %}
            <a href="{{ task.get_absolute_url }}">
              {{ task.name }}
            </a>
            {% else %}
            {{ task.name }}
            {% endif %}
          </td>
          <td>{{ task.completed }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      <a href="{{ object.get_override_url }}">Override</a>
    </body>
    </html>


The manual override view will also use the ``workflow_form.html`` template
that you have already created. You can of course create a more specific
template. Django will search for templates in the following order::

    app_name/welcomeworkflow_override.html
    app_name/workflow_override.html
    app_name/welcomeworkflow_form.html
    app_name/workflow_form.html

Last but not least you will need a template for the workflow detail view.
You don't really need to add anything here, but lets add a little information
to make your workflow feel more alive.



You are all set! Spin up your application and play around with it.

One more thing.  The "send_mail" task is supposed to run in the background, so
we will need a background worker to process it.  And since we don't want to 
really send mail, add this to the bottom of your ``settings.py`` file:

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

Now you can start a background worker to actually run the background tasks.  

    python manage.py rundramatiq --threads=1
    
**REVIEWERS:** I'm using Dramatiq + Redis (it's a personal problem)...do we
need instructions here on how to run a celery worker (that will work with 
SQLite?)

Once you are done come back to learn
:ref:`how to write tests in the next part of our tutorial<tutorial-testing>`.
