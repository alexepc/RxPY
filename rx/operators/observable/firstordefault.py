from typing import Any, Callable

from rx.core import AnonymousObservable, ObservableBase as Observable
from rx.core.typing import Predicate
from rx.internal.exceptions import SequenceContainsNoElementsError


def first_or_default_async(source, has_default=False, default_value=None):
    def subscribe(observer, scheduler=None):
        def on_next(x):
            observer.on_next(x)
            observer.on_completed()

        def on_completed():
            if not has_default:
                observer.on_error(SequenceContainsNoElementsError())
            else:
                observer.on_next(default_value)
                observer.on_completed()

        return source.subscribe_(on_next, observer.on_error, on_completed, scheduler)
    return AnonymousObservable(subscribe)


def first_or_default(predicate: Predicate = None, default_value: Any = None) -> Callable[[Observable], Observable]:
    """Returns the first element of an observable sequence that
    satisfies the condition in the predicate, or a default value if no
    such element exists.

    Examples:
        >>> res = source.first_or_default()
        >>> res = source.first_or_default(lambda x: x > 3)
        >>> res = source.first_or_default(lambda x: x > 3, 0)
        >>> res = source.first_or_default(null, 0)

    Args:
        source -- Observable sequence.
        predicate -- [optional] A predicate function to evaluate for
            elements in the source sequence.
        default_value -- [Optional] The default value if no such element
            exists.  If not specified, defaults to None.

    Returns:
        A function that takes an observable source and reutrn an
        observable sequence containing the first element in the
        observable sequence that satisfies the condition in the
        predicate, or a default value if no such element exists.
    """

    def partial(source: Observable) -> Observable:
        return source.filter(predicate).first_or_default(None, default_value) if predicate else first_or_default_async(source, True, default_value)
    return partial
