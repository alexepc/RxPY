from typing import Callable, Union
from datetime import timedelta
from rx.core import AnonymousObservable, Observable
from rx.concurrency import timeout_scheduler
from rx.internal.utils import add_ref
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable, RefCountDisposable, SerialDisposable
from rx.subjects import Subject


def window_with_time_or_count(timespan: Union[timedelta, int], count: int) -> Callable[[Observable], Observable]:
    def partial(source: Observable) -> Observable:
        def subscribe(observer, scheduler=None):
            scheduler = scheduler or timeout_scheduler

            n = [0]
            s = [None]
            timer_d = SerialDisposable()
            window_id = [0]
            group_disposable = CompositeDisposable(timer_d)
            ref_count_disposable = RefCountDisposable(group_disposable)

            def create_timer(_id):
                m = SingleAssignmentDisposable()
                timer_d.disposable = m

                def action(scheduler, state):
                    if _id != window_id[0]:
                        return

                    n[0] = 0
                    window_id[0] += 1
                    new_id = window_id[0]
                    s[0].on_completed()
                    s[0] = Subject()
                    observer.on_next(add_ref(s[0], ref_count_disposable))
                    create_timer(new_id)

                m.disposable = scheduler.schedule_relative(timespan, action)

            s[0] = Subject()
            observer.on_next(add_ref(s[0], ref_count_disposable))
            create_timer(0)

            def on_next(x):
                new_window = False
                new_id = 0

                s[0].on_next(x)
                n[0] += 1
                if n[0] == count:
                    new_window = True
                    n[0] = 0
                    window_id[0] += 1
                    new_id = window_id[0]
                    s[0].on_completed()
                    s[0] = Subject()
                    observer.on_next(add_ref(s[0], ref_count_disposable))

                if new_window:
                    create_timer(new_id)

            def on_error(e):
                s[0].on_error(e)
                observer.on_error(e)

            def on_completed():
                s[0].on_completed()
                observer.on_completed()

            group_disposable.add(source.subscribe_(on_next, on_error, on_completed, scheduler))
            return ref_count_disposable
        return AnonymousObservable(subscribe)
    return partial