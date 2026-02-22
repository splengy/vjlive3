import json
import logging
from typing import List, Dict, Optional, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)

class Cue:
    def __init__(self, cue_number: float, name: str, fade_in: float = 3.0, fade_out: float = 3.0, state: Dict[str, Any] = None) -> None:
        self.cue_number = float(cue_number)
        self.name = name
        self.fade_in = max(0.0, float(fade_in))
        self.fade_out = max(0.0, float(fade_out))
        self.state = state if state is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_number": self.cue_number,
            "name": self.name,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "state": self.state
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cue':
        return cls(
            cue_number=data.get("cue_number", 1.0),
            name=data.get("name", "Unnamed Cue"),
            fade_in=data.get("fade_in", 3.0),
            fade_out=data.get("fade_out", 3.0),
            state=data.get("state", {})
        )

class CueStack:
    def __init__(self, name: str = "Stack") -> None:
        self.name = name
        self._cues: Dict[float, Cue] = {}
        
        # State tracking
        self.current_cue: Optional[Cue] = None
        self.next_cue: Optional[Cue] = None
        
        self.is_fading = False
        self.is_halted = False
        
        self.fade_progress = 0.0
        self.fade_duration = 0.0
        
        self.active_state: Dict[str, Any] = {}
        self.origin_state: Dict[str, Any] = {}

    def add_cue(self, cue: Cue) -> None:
        self._cues[cue.cue_number] = cue
        # Keep sorted by cue number
        self._cues = OrderedDict(sorted(self._cues.items()))

    def remove_cue(self, cue_number: float) -> bool:
        if cue_number in self._cues:
            del self._cues[cue_number]
            return True
        return False

    def _get_sorted_cue_numbers(self) -> List[float]:
        return list(self._cues.keys())

    def go(self) -> None:
        if not self._cues:
            return

        cues = self._get_sorted_cue_numbers()
        
        if self.current_cue is None:
            # First cue go
            target_num = cues[0]
        else:
            # Next cue
            try:
                idx = cues.index(self.current_cue.cue_number)
                if idx + 1 < len(cues):
                    target_num = cues[idx + 1]
                else:
                    target_num = cues[-1] # Stay at end
            except ValueError:
                target_num = cues[0]

        self._trigger_transition(self._cues[target_num])

    def back(self) -> None:
        if not self._cues or self.current_cue is None:
            return

        cues = self._get_sorted_cue_numbers()
        try:
            idx = cues.index(self.current_cue.cue_number)
            if idx > 0:
                target_num = cues[idx - 1]
            else:
                target_num = cues[0]
        except ValueError:
            target_num = cues[0]
            
        self._trigger_transition(self._cues[target_num])

    def _trigger_transition(self, target_cue: Cue) -> None:
        self.is_halted = False
        # Save exact current progress state as the new origin so we can reverse mid-fade safely
        self.origin_state = dict(self.active_state)
        
        self.next_cue = target_cue
        self.fade_progress = 0.0
        self.fade_duration = target_cue.fade_in
        self.is_fading = True
        
        if self.fade_duration <= 0:
            # Snap instantly
            self.active_state = dict(target_cue.state)
            self.current_cue = target_cue
            self.next_cue = None
            self.is_fading = False

    def halt(self) -> None:
        self.is_halted = True

    def resume(self) -> None:
        self.is_halted = False

    def release(self, fade_time: float) -> None:
        self.is_halted = False
        self.origin_state = dict(self.active_state)
        self.current_cue = None
        
        # Release is just fading into an empty cue
        blackout = Cue(-1, "Release", fade_in=fade_time)
        self._trigger_transition(blackout)

    def process_frame(self, delta_time: float) -> Optional[Dict[str, Any]]:
        if not self.is_fading or self.is_halted:
            return self.active_state if self.current_cue or self.active_state else None
            
        if self.next_cue is None:
            self.is_fading = False
            return self.active_state
            
        self.fade_progress += delta_time
        
        if self.fade_progress >= self.fade_duration:
            # Fade complete
            self.active_state = dict(self.next_cue.state)
            self.current_cue = self.next_cue
            self.next_cue = None
            self.is_fading = False
            return self.active_state

        # Interpolation
        ratio = self.fade_progress / self.fade_duration
        target_state = self.next_cue.state
        
        # Combine keys from both origin and target
        all_keys = set(self.origin_state.keys()) | set(target_state.keys())
        
        new_active = {}
        for k in all_keys:
            orig_vals = self.origin_state.get(k, [])
            targ_vals = target_state.get(k, [])
            
            # Pad arrays if they differ in length (assume 0 for missing channels)
            max_len = max(len(orig_vals), len(targ_vals))
            orig_vals = list(orig_vals) + [0] * (max_len - len(orig_vals))
            targ_vals = list(targ_vals) + [0] * (max_len - len(targ_vals))
            
            interp_vals = []
            for o, t in zip(orig_vals, targ_vals):
                val = o + (t - o) * ratio
                interp_vals.append(max(0, min(255, int(val))))
                
            new_active[k] = interp_vals
            
        self.active_state = new_active
        return self.active_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cues": [cue.to_dict() for cue in self._cues.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CueStack':
        stack = cls(name=data.get("name", "Stack"))
        for c_data in data.get("cues", []):
            stack.add_cue(Cue.from_dict(c_data))
        return stack

class ShowController:
    def __init__(self) -> None:
        self.stacks: Dict[str, CueStack] = {}
        self.selected_stack_id: Optional[str] = None

    def add_stack(self, name: str) -> CueStack:
        stack = CueStack(name)
        self.stacks[name] = stack
        if self.selected_stack_id is None:
            self.selected_stack_id = name
        return stack

    def remove_stack(self, stack_id: str) -> bool:
        if stack_id in self.stacks:
            del self.stacks[stack_id]
            if self.selected_stack_id == stack_id:
                self.selected_stack_id = next(iter(self.stacks.keys())) if self.stacks else None
            return True
        return False

    def select_stack(self, stack_id: str) -> bool:
        if stack_id in self.stacks:
            self.selected_stack_id = stack_id
            return True
        return False

    def go(self) -> None:
        if self.selected_stack_id and self.selected_stack_id in self.stacks:
            self.stacks[self.selected_stack_id].go()

    def back(self) -> None:
        if self.selected_stack_id and self.selected_stack_id in self.stacks:
            self.stacks[self.selected_stack_id].back()

    def halt(self) -> None:
        if self.selected_stack_id and self.selected_stack_id in self.stacks:
            self.stacks[self.selected_stack_id].halt()

    def resume(self) -> None:
        if self.selected_stack_id and self.selected_stack_id in self.stacks:
            self.stacks[self.selected_stack_id].resume()

    def release(self, fade_time: float) -> None:
        if self.selected_stack_id and self.selected_stack_id in self.stacks:
            self.stacks[self.selected_stack_id].release(fade_time)

    def process_frame(self, delta_time: float) -> Dict[str, Any]:
        global_state = {}
        # HTP (Highest Takes Precedence) merge across all active stacks
        for stack in self.stacks.values():
            result = stack.process_frame(delta_time)
            if result:
                for fixture, channels in result.items():
                    if fixture not in global_state:
                        global_state[fixture] = list(channels)
                    else:
                        g_chans = global_state[fixture]
                        max_len = max(len(g_chans), len(channels))
                        g_chans += [0] * (max_len - len(g_chans))
                        channels = list(channels) + [0] * (max_len - len(channels))
                        
                        for i in range(max_len):
                            g_chans[i] = max(g_chans[i], channels[i])
                        global_state[fixture] = g_chans

        return global_state

    def save_show(self, filepath: str) -> bool:
        try:
            data = self.to_dict()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save show to {filepath}: {e}")
            return False

    def load_show(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            new_ctrl = ShowController.from_dict(data)
            self.stacks = new_ctrl.stacks
            self.selected_stack_id = new_ctrl.selected_stack_id
            return True
        except Exception as e:
            logger.error(f"Failed to load show from {filepath}: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_stack": self.selected_stack_id,
            "stacks": {id: stack.to_dict() for id, stack in self.stacks.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShowController':
        ctrl = cls()
        ctrl.selected_stack_id = data.get("selected_stack")
        for s_id, s_data in data.get("stacks", {}).items():
            ctrl.stacks[s_id] = CueStack.from_dict(s_data)
        return ctrl
