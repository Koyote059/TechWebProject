import json
from json import JSONDecodeError
from pprint import pprint

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import DetailView, TemplateView, UpdateView, FormView

from GymApp.models import GymUser
from GymApp.utils import send_pdf, _get_or_error
from base_views import SearchListView
from workout.models import WorkoutPlan, Exercise, ExerciseSet, WorkoutDay


class UserWorkoutPlanView(DetailView):
    model = WorkoutPlan
    template_name = 'workout_detail.html'
    context_object_name = 'workoutPlan'

    def get_object(self, queryset=None):
        user = self.request.user
        index = int(self.request.GET.get('index')) if self.request.GET.get('index') else 0
        if index:
            try:
                return WorkoutPlan.objects.filter(user=user).order_by('-created')[int(index)]
            except IndexError:
                return None
        else:
            try:
                return WorkoutPlan.objects.filter(user=user).order_by('-created')[index]
            except IndexError:
                return None

    def get_context_data(self, **kwargs):
        total_workouts = WorkoutPlan.objects.filter(user=self.request.user).count()
        index = int(self.request.GET.get('index')) if self.request.GET.get('index') else 0
        prev_workout_url = reverse_lazy(
            'workout') + f'?index={index - 1}' if index > 0 else None
        next_workout_url = reverse_lazy('workout') + f'?index={index + 1}' \
            if index < total_workouts - 1 else None

        context = super().get_context_data(**kwargs)
        context['prev_workout_url'] = prev_workout_url
        context['next_workout_url'] = next_workout_url
        context['index'] = index
        return context


@require_GET
def download_workout(request):
    index = int(request.GET.get('index')) if request.GET.get('index') else 0
    workout = WorkoutPlan.objects.filter(user=request.user).order_by('-created')[index]
    rendered_html = render_to_string('workout_pdf.html', {'workoutPlan': workout})
    return send_pdf(rendered_html, f'workout_{index}')


class ManageWorkoutsView(SearchListView):
    template_name = 'manage_workouts.html'

    def __init__(self):
        super().__init__(GymUser, 'username', 'gymusers', 10)

    def search(self, string: str):
        return GymUser.objects.filter(username__istartswith=string)

    def get_url(self, obj) -> str:
        if WorkoutPlan.objects.filter(user=obj, actual_end_date=None).exists():
            return f'/workout/manage/updateWorkout/{obj.username}'
        return f'/workout/manage/createWorkout/{obj.username}'

    def get_name(self, obj) -> str:
        return obj.username


class CreateWorkoutView(TemplateView):
    template_name = 'workout_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exercises'] = {exercise.id: exercise.name for exercise in Exercise.objects.all()}
        context['userName'] = self.kwargs['userName']
        return context


class UpdateWorkoutView(TemplateView):
    template_name = 'workout_update.html'

    def get_object(self, queryset=None):
        user = self.request.user
        try:
            return WorkoutPlan.objects.filter(user=user, actual_end_date=None).order_by('-created')[0]
        except IndexError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['userName'] = self.request.user.username
        context['exercises'] = {exercise.id: exercise.name for exercise in Exercise.objects.all()}
        obj = self.get_object()
        workoutPlanJson = {
            'id': obj.id,
            'expected_end_date': str(obj.expected_end_date),
            'days': [
                {
                    'exercises': [
                        {
                            'exercise': exerciseSet.exercise.id,
                            'reps': exerciseSet.reps,
                            'sets': exerciseSet.sets
                        } for exerciseSet in day.exercise_sets.all()]

                } for day in obj.workout_days.all()
            ]
        }
        context['workoutPlan'] = json.dumps(workoutPlanJson)
        return context


@require_POST
def save_workout(request, userName):
    try:
        body = json.loads(request.body)
        days = _get_or_error(body, 'days', list)
        expirationDay = _get_or_error(body, 'expirationDay', str)
        user = GymUser.objects.get(username=userName)
        workoutId = body.get('id')
        if workoutId:
            workoutPlan = WorkoutPlan.objects.get(id=workoutId)
            workoutPlan.expected_end_date = expirationDay
            for workoutDay in workoutPlan.workout_days.all():
                workoutDay.exercise_sets.all().delete()
            workoutPlan.workout_days.all().delete()
        else:
            workoutPlan = WorkoutPlan(user=user, expected_end_date=expirationDay)
        workoutPlan.save()
        for dayObj in days:
            workoutDay = WorkoutDay(workout_plan=workoutPlan)
            workoutDay.save()
            for exerciseObj in _get_or_error(dayObj, 'exercises', list):
                exerciseId = _get_or_error(exerciseObj, 'exercise', int)
                reps = _get_or_error(exerciseObj, 'reps', int)
                sets = _get_or_error(exerciseObj, 'sets', int)
                exercise = Exercise.objects.get(id=exerciseId)
                exerciseSet = ExerciseSet(exercise=exercise, reps=reps, sets=sets, workout_day=workoutDay)
                exerciseSet.save()
    except JSONDecodeError:
        return HttpResponse(status=400, content='Invalid JSON')
    except ValueError:
        return HttpResponse(status=400, content='Invalid value')
    except GymUser.DoesNotExist:
        return HttpResponse(status=404, content='User not found')
    return HttpResponse(status=200)
