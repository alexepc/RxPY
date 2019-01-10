from rx.core import Observable, AnonymousObservable, Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable, SerialDisposable
from rx.concurrency import current_thread_scheduler
from rx.internal import Iterable


def _catch_exception(*args: Observable) -> Observable:
    """Continues an observable sequence that is terminated by an
    exception with the next observable sequence.

    Examples:
        >>> res = catch_exception(xs, ys, zs)
        >>> res = catch_exception([xs, ys, zs])

    Returns:
        An observable sequence containing elements from consecutive
        source sequences until a source sequence terminates
        successfully.
    """

    if isinstance(args[0], (list, Iterable)):
        sources = args[0]
    else:
        sources = list(args)

    def subscribe(observer, scheduler=None):
        scheduler = scheduler or current_thread_scheduler

        subscription = SerialDisposable()
        cancelable = SerialDisposable()
        last_exception = [None]
        is_disposed = []
        e = iter(sources)

        def action(action1, state=None):
            def on_error(exn):
                last_exception[0] = exn
                cancelable.disposable = scheduler.schedule(action)

            if is_disposed:
                return

            try:
                current = next(e)
            except StopIteration:
                if last_exception[0]:
                    observer.on_error(last_exception[0])
                else:
                    observer.on_completed()
            except Exception as ex:  # pylint: disable=broad-except
                observer.on_error(ex)
            else:
                d = SingleAssignmentDisposable()
                subscription.disposable = d
                d.disposable = current.subscribe_(observer.on_next, on_error, observer.on_completed, scheduler)

        cancelable.disposable = scheduler.schedule(action)

        def dispose():
            is_disposed.append(True)
        return CompositeDisposable(subscription, cancelable, Disposable.create(dispose))
    return AnonymousObservable(subscribe)