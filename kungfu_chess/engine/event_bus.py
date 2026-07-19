"""
שכבה: Engine
event_bus.py — ערוץ מרכזי להעברת אירועים (Pub/Sub pattern).

GameEngine שולח אירועים ל-Bus.
Bus מעביר לכל מי שנרשם.
אף אחד לא מכיר את השני ישירות.

שימוש:
    bus = EventBus()
    bus.subscribe("piece_captured", my_function)
    bus.publish("piece_captured", {"piece": ..., "value": 5})
"""


class EventBus:
    """
    ערוץ אירועים מרכזי.
    subscribe — נרשם לאירוע מסוים.
    publish — שולח אירוע לכל מי שנרשם.
    """

    def __init__(self):
        self._subscribers = {}  # event_name -> list of callbacks

    def subscribe(self, event_name: str, callback):
        """
        נרשם לקבל הודעות על אירוע מסוים.
        callback: פונקציה שתיקרא כשהאירוע קורה. מקבלת dict עם נתונים.
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, data: dict = None):
        """
        שולח אירוע לכל מי שנרשם.
        event_name: שם האירוע (למשל "piece_captured")
        data: dict עם נתונים על האירוע
        """
        if data is None:
            data = {}
        callbacks = self._subscribers.get(event_name, [])
        for callback in callbacks:
            callback(data)
