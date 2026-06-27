from __future__ import annotations

import re

_RULES: list[tuple[str, str]] = [
    (r"timeout.*exceeded|locator\..*timeout|waiting for.*timeout",
     "The element did not appear or respond within the time limit"),
    (r"tobevisible|to be visible|expected.*visible",
     "An expected element was not visible on the page"),
    (r"tobehidden|to be hidden|expected.*hidden",
     "An element was still visible on the page when it should have been hidden"),
    (r"tobeenabled|to be enabled",
     "A button or field was disabled when it should have been active"),
    (r"tobechecked|to be checked",
     "A checkbox or radio button was not in the expected state"),
    (r"net::err_connection_refused|econnrefused|connection refused",
     "The application was not reachable, it may not be running"),
    (r"net::err_name_not_resolved|getaddrinfo|dns",
     "The application URL could not be resolved, check the base URL"),
    (r"navigation.*timeout|page.*timeout|waiting for.*navigation",
     "The page took too long to load"),
    (r"strict mode violation|resolved to \d+ elements",
     "Multiple elements matched where only one was expected, the selector is too broad"),
    (r"element is not an input|element is not editable|not editable",
     "Tried to type into an element that does not accept text input"),
    (r"element.*intercept|covered by another element|intercept.*pointer",
     "The element was blocked by another element on the page"),
    (r"detached|element.*not attached|handle.*disposed",
     "The element disappeared from the page before the action could complete"),
    (r"tobehaveurl|expected url|tohaveurl",
     "The page navigated to the wrong URL"),
    (r"tohavetext|tocontaintext|expected.*text|text.*expected",
     "The text on the page did not match what was expected"),
    (r"tohavetitle|expected title",
     "The page title did not match what was expected"),
    (r"tohavevalue|expected value",
     "A form field contained a different value than expected"),
    (r"401|unauthorized|unauthenticated",
     "The user was not authenticated, login may have failed"),
    (r"403|forbidden|access denied",
     "The user did not have permission to access this page"),
    (r"404|not found",
     "The page or resource was not found"),
    (r"500|internal server error|server error",
     "The application returned a server error"),
    (r"cannot read.*propert|undefined is not|null is not|typeerror",
     "The application hit a JavaScript error during the test"),
    (r"expect.*tobe\b|tobetruthy|tobefalsy|expected.*equal",
     "A value in the test did not match the expected result"),
    (r"screenshot|visual.*compar|image.*diff",
     "The page looked different from the approved reference screenshot"),
    (r"locator\.click|locator\.fill|locator\.select|locator\.check",
     "Could not interact with the element, it may not exist or not be ready"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), e) for p, e in _RULES]
_FALLBACK = "The test failed with an unexpected error"


def explain(error_message: str, stack_trace: str) -> str:
    combined = error_message + " " + stack_trace
    for pattern, explanation in _COMPILED:
        if pattern.search(combined):
            return explanation
    return _FALLBACK
