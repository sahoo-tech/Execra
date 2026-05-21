import sys
from typing import Optional, Any


class CodeTracer:
    def __init__(self) -> None:
        self._events: list[dict] = []
        self.target_module: str = ""
        self.event_count: int = 0
        self.current_depth: int = 0
        self.max_depth_seen: int = 0
        self.is_active: bool = False
        self.RECURSION_LIMIT = 1000
        self.EVENT_LIMIT = 10000

    def start_trace(self,target_module_name:str):
        self.target_module = target_module_name

        # Reset state
        self._events = []
        self.event_count = 0
        self.current_depth = 0
        self.max_depth_seen = 0

        # Active
        self.is_active = True
        sys.settrace(self._trace_handler)

    
    def stop_trace(self) -> None:
        self.is_active = False
        sys.settrace(None)

    
    def _trace_handler(self,frame, event, arg):

        # Threshold checking
        if self.event_count >= self.EVENT_LIMIT or self.current_depth >= self.RECURSION_LIMIT:
            self.is_active = False
            sys.settrace(None)
            return None

        # Filtering non-targeting modules
        if not frame.f_globals.get("__name__", "").startswith(self.target_module):
            return self._trace_handler

        # Record Event
        record ={
            "event_type": event,
            "function": frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "args":{},
            "return_value": None,
            "exception": None 
        }

        # Handles call event
        if event == "call":

            self.current_depth += 1
            if self.current_depth > self.max_depth_seen:
                self.max_depth_seen = self.current_depth
            
            record["args"] = {k: str(v) for k, v in frame.f_locals.items()}

        # Handles return event
        if event == "return":
            self.current_depth -= 1
            record["return_value"] = str(arg)

        # Handles exception event
        if event == "exception":
            exc_type, exc_value, tb = arg
            record["exception"] = f"{exc_type.__name__}: {exc_value}"

        # Finalize event recording
        self._events.append(record)
        self.event_count += 1


        return self._trace_handler
    
    def get_trace_log(self) -> list[dict]:
        return self._events
    
    def get_summary(self):

        summary = {
            "total_calls": len([1 for event in self._events if event["event_type"] == "call"]),

            "total_lines": len([1 for event in self._events if event["event_type"]== "line"]),

            "exceptions_caught": len([1 for event in self._events if event["event_type"]== "exception"]),

            "max_recursion_depth": self.max_depth_seen,

            "execution_path": [event["function"] for event in self._events if event["event_type"] == "call"]
        }

        return summary
    
# Shared Instance
code_tracer = CodeTracer()