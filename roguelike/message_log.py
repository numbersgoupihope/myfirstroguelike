"""Rolling, word-wrapped message log shown in the bottom panel."""

import textwrap


class Message:
    __slots__ = ("text", "color")

    def __init__(self, text, color="msg_info"):
        self.text = text
        self.color = color


class MessageLog:
    def __init__(self, width, max_lines=200):
        self.messages = []
        self.width = width
        self.max_lines = max_lines

    def add(self, text, color="msg_info"):
        for line in textwrap.wrap(text, self.width):
            self.messages.append(Message(line, color))
        while len(self.messages) > self.max_lines:
            self.messages.pop(0)

    def extend_results(self, results):
        """Convenience: pull any {"message": Message(...)} entries out of an
        action-result list and add them in order."""
        for result in results:
            message = result.get("message") if isinstance(result, dict) else None
            if message:
                self.add(message.text, message.color)
